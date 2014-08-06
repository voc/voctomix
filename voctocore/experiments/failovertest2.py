#!/usr/bin/python3

from os import path

import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst


GObject.threads_init()
Gst.init(None)

class FramegrabberSource(Gst.Bin):
    def __init__(self, uri, caps):
        super().__init__()
        self.caps = caps

        # Create elements
        self.http = Gst.ElementFactory.make('souphttpsrc', None)
        self.demux = Gst.ElementFactory.make('multipartdemux', None)
        self.parse = Gst.ElementFactory.make('jpegparse', None)
        self.dec = Gst.ElementFactory.make('jpegdec', None)
        self.queue = Gst.ElementFactory.make('queue', None)

        # Add elements to Bin
        self.add(self.http)
        self.add(self.parse)
        self.add(self.demux)
        self.add(self.dec)
        self.add(self.queue)
        
        # Set properties
        self.http.set_property('location', uri)
        self.http.set_property('timeout', 5)
        #self.http.set_property('is-live', True)
        #self.http.set_property('do-timestamp', True)
        
        # Connect signal handlers
        self.demux.connect('pad-added', self.on_demux_pad_added)
        self.queue.connect('underrun', self.on_queue_underrun)
        self.queue.connect('running', self.on_queue_running)
        self.queue.connect('pushing', self.on_queue_pushing)
        
        # Link elements
        self.http.link(self.demux)
        # dynamic linked # self.demux.link(self.parse)
        self.parse.link(self.dec)
        self.dec.link(self.queue)

        # Add Ghost Pads
        self.add_pad(
            Gst.GhostPad.new('src', self.queue.get_static_pad('src'))
        )
    
    def on_demux_pad_added(self, element, pad):
        string = pad.query_caps(None).to_string()
        print('on_demux_pad_added():', string)
        if string.startswith('image/jpeg'):
            pad.link(self.parse.get_static_pad('sink'))
    
    def on_queue_underrun(self, queue):
        print('on_queue_underrun()')
    
    def on_queue_running(self, queue):
        print('on_queue_running()')
    
    def on_queue_pushing(self, queue):
        print('on_queue_pushing()')


class VideomixerWithDisplay(Gst.Bin):
    def __init__(self):
        super().__init__()
        
        # Create elements
        self.secondsrc = Gst.ElementFactory.make('videotestsrc', None)
        self.mixer = Gst.ElementFactory.make('videomixer', None)
        self.display = Gst.ElementFactory.make('ximagesink', None)
        
        # Add elements to Bin
        self.add(self.secondsrc)
        self.add(self.mixer)
        self.add(self.display)
        
        # Set properties
        self.secondsrc.set_property('pattern', 'ball')
        
        # Request Pads
        self.firstpad = self.mixer.get_request_pad('sink_%u')
        self.secondpad = self.mixer.get_request_pad('sink_%u')
        
        # Set pad-properties
        self.secondpad.set_property('alpha', 0.7)
        self.secondpad.set_property('xpos', 50)
        self.secondpad.set_property('ypos', 50)
        
        # Link elements
        self.secondsrc.get_static_pad('src').link(self.secondpad)
        self.mixer.link(self.display)
        
        # Add Ghost Pads
        self.add_pad(
            Gst.GhostPad.new('sink', self.firstpad)
        )



class Example:
    def __init__(self):        
        self.mainloop = GObject.MainLoop()
        self.pipeline = Gst.Pipeline()
        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect('message::eos', self.on_eos)
        self.bus.connect('message::error', self.on_error)

        # Create elements
        self.grabbersrc = FramegrabberSource(
            uri='http://beachcam.kdhnc.com/mjpg/video.mjpg?camera=1',
            caps=Gst.caps_from_string('image/jpeg,framerate=1/1'))

        self.mixdisplay = VideomixerWithDisplay()

        # Add elements to pipeline      
        self.pipeline.add(self.grabbersrc)
        self.pipeline.add(self.mixdisplay)

        self.grabbersrc.link(self.mixdisplay)

    def run(self):
        self.pipeline.set_state(Gst.State.PLAYING)
        self.mainloop.run()

    def kill(self):
        self.pipeline.set_state(Gst.State.NULL)
        self.mainloop.quit()

    def on_eos(self, bus, msg):
        print('on_eos()')
        self.kill()

    def on_error(self, bus, msg):
        print('on_error():', msg.parse_error())
        self.kill()


example = Example()
example.run()
