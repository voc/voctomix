#!/usr/bin/python3

from os import path

import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst


GObject.threads_init()
Gst.init(None)

class FramegrabberSource(Gst.Bin):
    def __init__(self, uri):
        super().__init__()

        # Create elements
        self.http = Gst.ElementFactory.make('souphttpsrc', None)
        self.demux = Gst.ElementFactory.make('multipartdemux', None)
        self.parse = Gst.ElementFactory.make('jpegparse', None)
        self.dec = Gst.ElementFactory.make('jpegdec', None)

        # Add elements to Bin
        self.add(self.http)
        self.add(self.parse)
        self.add(self.demux)
        self.add(self.dec)
        
        # Set properties
        self.http.set_property('location', uri)
        self.http.set_property('timeout', 5)
        #self.http.set_property('is-live', True)
        #self.http.set_property('do-timestamp', True)
        
        # Connect signal handlers
        self.demux.connect('pad-added', self.on_demux_pad_added)
        
        # Link elements
        self.http.link(self.demux)
        # dynamic linked # self.demux.link(self.parse)
        self.parse.link(self.dec)   
        
        # Add Ghost Pads
        self.add_pad(
            Gst.GhostPad.new('src', self.dec.get_static_pad('src'))
        )

    def on_demux_pad_added(self, element, pad):
        string = pad.query_caps(None).to_string()
        print('on_demux_pad_added():', string)
        if string.startswith('image/jpeg'):
            pad.link(self.parse.get_static_pad('sink'))


class FailoverFilter(Gst.Bin):
    def __init__(self):
        super().__init__()
        
        self.queue = Gst.ElementFactory.make('queue', None)
        self.failsrc = Gst.ElementFactory.make('videotestsrc', None)
        self.capsfilter = Gst.ElementFactory.make('capsfilter', None)
        self.switch = Gst.ElementFactory.make('input-selector', "sw")
        
        # Add elements to Bin
        self.add(self.queue)
        self.add(self.failsrc)
        self.add(self.capsfilter)
        self.add(self.switch)
        
        # Request Pads
        self.goodpad = self.switch.get_request_pad('sink_%u')
        self.failpad = self.switch.get_request_pad('sink_%u')
        
        # Set properties
        self.switch.set_property('active-pad', self.goodpad)
        self.capsfilter.set_property('caps', Gst.Caps.from_string('video/x-raw,format=I420,width=640,height=480'))
        
        # Connect signal handlers
        self.queue.connect('underrun', self.on_queue)
        self.queue.connect('running', self.on_queue)
        
        # Link elements
        self.queue.get_static_pad('src').link(self.goodpad)
        self.failsrc.link(self.capsfilter)
        self.capsfilter.get_static_pad('src').link(self.failpad)
        
        # Add Ghost Pads
        self.add_pad(
            Gst.GhostPad.new('sink', self.queue.get_static_pad('sink'))
        )
        self.add_pad(
            Gst.GhostPad.new('src', self.switch.get_static_pad('src'))
        )
    
    def on_queue(self, queue):
        level = queue.get_property('current-level-buffers')
        print('on_queue()', level)
        switch = queue.get_parent().get_by_name("sw")
        switch.set_property('active-pad', switch.get_static_pad('sink_1' if level == 0 else 'sink_0'))

class VideomixerWithDisplay(Gst.Bin):
    def __init__(self):
        super().__init__()
        
        # Create elements
        self.secondsrc = Gst.ElementFactory.make('videotestsrc', None)
        self.mixer = Gst.ElementFactory.make('videomixer', None)
        self.q1 = Gst.ElementFactory.make('queue', None)
        self.q2 = Gst.ElementFactory.make('queue', None)
        self.display = Gst.ElementFactory.make('ximagesink', None)
        
        # Add elements to Bin
        self.add(self.secondsrc)
        self.add(self.mixer)
        self.add(self.display)
        self.add(self.q1)
        self.add(self.q2)
        
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
        self.q1.get_static_pad('src').link(self.firstpad)
        
        self.q2.get_static_pad('src').link(self.secondpad)
        self.secondsrc.link(self.q2)

        self.mixer.link(self.display)
        
        # Add Ghost Pads
        self.add_pad(
            Gst.GhostPad.new('sink', self.q1.get_static_pad('sink'))
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
            uri='http://beachcam.kdhnc.com/mjpg/video.mjpg?camera=1')
        
        self.failover = FailoverFilter()
        self.mixdisplay = VideomixerWithDisplay()

        # Add elements to pipeline      
        self.pipeline.add(self.grabbersrc)
        self.pipeline.add(self.failover)
        self.pipeline.add(self.mixdisplay)

        self.grabbersrc.link(self.failover)
        self.failover.link(self.mixdisplay)

    def run(self):
        self.pipeline.set_state(Gst.State.PLAYING)
        self.mainloop.run()

    def kill(self):
        self.pipeline.set_state(Gst.State.NULL)
        self.mainloop.quit()

    def on_eos(self, bus, msg):
        print('on_eos()')
        #self.kill()

    def on_error(self, bus, msg):
        print('on_error():', msg.parse_error())
        #self.kill()


example = Example()
example.run()
