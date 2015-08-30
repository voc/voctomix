#!/usr/bin/python3
import gi, time
import socket

# import GStreamer and GTK-Helper classes
gi.require_version('Gst', '1.0')
from gi.repository import GLib, Gst, GObject

# init GObject before importing local classes
GObject.threads_init()
Gst.init(None)

class Example:
	def __init__(self):
		self.mainloop = GObject.MainLoop()
		self.source_pipeline = None

		video = True
		if video:
			self.pipeline1 = Gst.parse_launch("""
				videotestsrc !
					video/x-raw,width=800,height=450,format=I420,framerate=1/1 !
					intervideosink channel=video
			""")

			self.pipeline2 = Gst.parse_launch("""
				intervideosrc channel=video !
					video/x-raw,width=800,height=450,format=I420,framerate=1/1 !
					xvimagesink
			""")

		else:
			self.pipeline1 = Gst.parse_launch("""
				audiotestsrc !
					audio/x-raw,format=S16LE,channels=2,layout=interleaved,rate=48000,channel-mask=(bitmask)0x3 !
					interaudiosink channel=audio
			""")

			self.pipeline2 = Gst.parse_launch("""
				interaudiosrc channel=audio !
					audio/x-raw,format=S16LE,channels=2,layout=interleaved,rate=48000,channel-mask=(bitmask)0x3 !
					alsasink
			""")

		self.pipeline1.bus.add_signal_watch()
		self.pipeline1.bus.connect("message::eos", self.on_eos)
		self.pipeline1.bus.connect("message::error", self.on_error)

		self.pipeline2.bus.add_signal_watch()
		self.pipeline2.bus.connect("message::eos", self.on_eos)
		self.pipeline2.bus.connect("message::error", self.on_error)

		GLib.timeout_add_seconds(3, self.on_timeout)

	def run(self):
		print("starting pipeline2")
		self.pipeline2.set_state(Gst.State.PLAYING)
		self.mainloop.run()

	def on_timeout(self):
		print("starting pipeline1")
		self.pipeline1.set_state(Gst.State.PLAYING)
		return False

	def on_eos(self, bus, message):
		self.log.debug('Received End-of-Stream-Signal on Pipeline')

	def on_error(self, bus, message):
		self.log.debug('Received Error-Signal on Pipeline')
		(error, debug) = message.parse_error()
		self.log.debug('Error-Details: #%u: %s', error.code, debug)

example = Example()
example.run()
