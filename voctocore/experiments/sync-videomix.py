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
			videoscale !
			capsfilter name=caps0 !
			identity sync=true signal-handoffs=false !
			mix.

			videotestsrc pattern=green !
			{caps} !
			videoscale !
			capsfilter name=caps1 !
			identity sync=true signal-handoffs=false !
			mix.

			videomixer name=mix !
			{caps} !
			identity name=sig !
			videoconvert !
			pngenc !
			multifilesink location=frame%04d.png
		""".format(
			caps='video/x-raw,width=800,height=450,format=I420,framerate=25/1'
		)

		self.pipeline = Gst.parse_launch(pipeline)
		sig = self.pipeline.get_by_name('sig')
		sig.connect('handoff', self.handoff)

		self.pad0 = self.pipeline.get_by_name('mix').get_static_pad('sink_0')
		self.pad1 = self.pipeline.get_by_name('mix').get_static_pad('sink_1')

		self.caps0 = self.pipeline.get_by_name('caps0')
		self.caps1 = self.pipeline.get_by_name('caps1')

		self.state = False

	def handoff(self, object, buffer):

		if self.state:
			padA = self.pad0
			padB = self.pad1
			capsA = self.caps0
			capsB = self.caps1
		else:
			padA = self.pad1
			padB = self.pad0
			capsA = self.caps1
			capsB = self.caps0

		padA.set_property('xpos', 10)
		padA.set_property('ypos', 10)
		padA.set_property('alpha', 1.0)
		padA.set_property('zorder', 1)
		capsA.set_property('caps', Gst.Caps.from_string('video/x-raw,width=400,height=225'))

		padB.set_property('xpos', 390)
		padB.set_property('ypos', 215)
		padB.set_property('alpha', 1.0)
		padB.set_property('zorder', 2)
		capsB.set_property('caps', Gst.Caps.from_string('video/x-raw,width=400,height=225'))

		self.state = not self.state

	def run(self):
		self.pipeline.set_state(Gst.State.PLAYING)
		self.mainloop.run()

	def kill(self):
		self.pipeline.set_state(Gst.State.NULL)
		self.mainloop.quit()

example = Example()
example.run()
