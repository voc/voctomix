#!/usr/bin/python3

from os import path

import threading
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
    failcount = 1 # start initially failed
    watchdogcount = 1
    dead = False
    
    def __init__(self):
        super().__init__()
        
        self.queue = Gst.ElementFactory.make('queue', None)
        self.failsrc = Gst.ElementFactory.make('videotestsrc', None)
        self.capsfilter = Gst.ElementFactory.make('capsfilter', None)
        self.switch = Gst.ElementFactory.make('input-selector', None)
        
        # Add elements to Bin
        self.add(self.queue)
        self.add(self.failsrc)
        self.add(self.capsfilter)
        self.add(self.switch)
        
        # Request Pads
        self.goodpad = self.switch.get_request_pad('sink_%u')
        self.failpad = self.switch.get_request_pad('sink_%u')
        
        # Set properties
        self.switch.set_property('active-pad', self.failpad)
        self.capsfilter.set_property('caps', Gst.Caps.from_string('video/x-raw,format=I420,width=640,height=480'))
        
        # Connect signal handlers
        self.queue.connect('underrun', self.underrun)
        self.queue.connect('overrun', self.overrun)
        self.queue.connect('running', self.running)
        self.queue.connect('pushing', self.pushing)
        
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
        
        # Setup signals
        for signalname in ('watchdog', 'switch-to-fail', 'switch-to-good', 'dead', 'reanimate'):
            GObject.signal_new(
                signalname,
                self,
                GObject.SIGNAL_RUN_LAST,
                GObject.TYPE_NONE,
                []
            )
        
        self.connect('reanimate', self.reanimate)
        
        # Start watchdog
        self.watchdog()
    
    def reanimate(self, caller=None):
        print('reanimate()')
        self.failcount = 1
        self.watchdogcount = 1
        self.dead = False
    
    def watchdog(self):
        if self.dead:
            return
        
        self.watchdogtimer = threading.Timer(0.5, self.watchdog)
        self.watchdogtimer.start()
        
        self.emit('watchdog')
        
        if self.failcount == 0:
            self.watchdogcount = 0
            if self.switch.get_property('active-pad') != self.goodpad:
                print("watchdog switching to goodpad")
                self.switch.set_property('active-pad', self.goodpad)
                self.emit('switch-to-good')
        else:
            self.watchdogcount += 1
            if self.switch.get_property('active-pad') != self.failpad:
                print("watchdog switching to failpad")
                self.switch.set_property('active-pad', self.failpad)
                self.emit('switch-to-fail')
            
            print("self.watchdogcount=", self.watchdogcount)
            if self.watchdogcount > 20:
                print("watchdog giving up -> source is dead")
                self.dead = True
                self.emit('dead')
    
    def underrun(self, queue):
        level = queue.get_property('current-level-buffers')
        
        failbin = queue.get_parent()
        if level == 0:
            failbin.failcount += 1
        
        print('underrun(), level=', level, 'failcount=', failbin.failcount)
    
    def overrun(self, queue):
        level = queue.get_property('current-level-buffers')
        
        failbin = queue.get_parent()
        if level > 0:
            failbin.failcount = 0
        
        print('overrun(), level=', level, 'failcount=', failbin.failcount)
    
    def running(self, queue):
        level = queue.get_property('current-level-buffers')
        print('running(), level=', level)
    
    def pushing(self, queue):
        level = queue.get_property('current-level-buffers')
        
        failbin = queue.get_parent()
        if level == 0:
            failbin.failcount += 1
        
        print('pushing(), level=', level, 'failcount=', failbin.failcount)

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
        
        self.failover.connect('dead', self.grabbersrc_is_dead)

    def grabbersrc_is_dead(self, failover):
        print("grabbersrc_is_dead", failover)
        self.pipeline.set_state(Gst.State.PAUSED)
        print(self.grabbersrc.unlink(self.failover))
        self.pipeline.remove(self.grabbersrc)
        self.grabbersrc = FramegrabberSource(
            uri='http://beachcam.kdhnc.com/mjpg/video.mjpg?camera=1')
        self.pipeline.add(self.grabbersrc)
        print(self.grabbersrc.link(self.failover))
        self.failover.reanimate()
        self.pipeline.set_state(Gst.State.PLAYING)

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
