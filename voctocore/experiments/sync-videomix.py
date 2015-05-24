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

		pipeline = """
			videotestsrc pattern=red !
			{caps} !
			identity sync=true signal-handoffs=false !
			mix.

			videotestsrc pattern=green !
			{caps} !
			identity sync=true signal-handoffs=false !
			mix.

			videomixer name=mix !
			{caps} !
			identity name=sig !
			videoconvert !
			pngenc !
			multifilesink location=frame%04d.png
		""".format(
			caps='video/x-raw,height=450,width=800,format=I420,framerate=25/1'
		)

		self.pipeline = Gst.parse_launch(pipeline)
		sig = self.pipeline.get_by_name('sig')
		sig.connect('handoff', self.handoff)

		self.mix = self.pipeline.get_by_name('mix')
		self.state = 0

	def handoff(self, object, buffer):
		mixerpad = self.mix.get_static_pad('sink_1')

		print('handoff, alpha=%u' % self.state)
		mixerpad.set_property('alpha', self.state)
		self.state = 0 if self.state else 1

	def run(self):
		self.pipeline.set_state(Gst.State.PLAYING)
		self.mainloop.run()

	def kill(self):
		self.pipeline.set_state(Gst.State.NULL)
		self.mainloop.quit()

example = Example()
example.run()
