#!/usr/bin/python3
import gi

# import GStreamer and GTK-Helper classes
gi.require_version('Gst', '1.0')
from gi.repository import GLib, Gst, GObject

# init GObject before importing local classes
GObject.threads_init()
Gst.init(None)

from videodisplay import VideomixerWithDisplay
from shmsrc import ShmSrc

class Example:
	def __init__(self):
		self.mainloop = GObject.MainLoop()
		self.pipeline = Gst.Pipeline()

		self.bus = self.pipeline.get_bus()
		self.bus.add_signal_watch()
		self.bus.connect('message::eos', self.on_eos)
		self.bus.connect('message::error', self.on_error)

		self.mixdisplay = VideomixerWithDisplay()
		self.grabbersrc = ShmSrc('/tmp/grabber', Gst.Caps.from_string('video/x-raw,width=1280,height=720,framerate=25/1,format=BGRA'))

		# Add elements to pipeline
		self.pipeline.add(self.mixdisplay)
		self.pipeline.add(self.grabbersrc)

		self.grabbersrc.link(self.mixdisplay)

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
