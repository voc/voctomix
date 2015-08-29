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
			mix.

			videotestsrc pattern=green !
			{caps} !
			mix.

			compositor name=mix !
			{caps} !
			identity name=sig !
			videoconvert !
			pngenc !
			multifilesink location=frame%04d.png
		""".format(
			caps='video/x-raw,width=800,height=450,format=I420,framerate=25/1'
		)

		self.pipeline = Gst.parse_launch(pipeline)

		# with sync=False changes to videomixer & scaler are performed
		# from the main thread. In the frame-images it becomes clear, that
		# sometimes not all changes are applied before a frame is pushed
		# through the mixer, and so there are "half modified" frames where
		# some pieces are missing, the zorder or the size of one video is
		# incorrect
		# with sync=True all changes are made from the streaming-thread
		# that drives the videomixer and the following elements, so they
		# are always completed before the mixer processes the next frame
		sync = True
		if sync:
			sig = self.pipeline.get_by_name('sig')
			sig.connect('handoff', self.reconfigure)
		else:
			GLib.timeout_add(1/25 * 1000, self.reconfigure, 0, 0)

		self.pad0 = self.pipeline.get_by_name('mix').get_static_pad('sink_0')
		self.pad1 = self.pipeline.get_by_name('mix').get_static_pad('sink_1')

		self.state = False

	def reconfigure(self, object, buffer):
		print("reconfigure!")
		if self.state:
			padA = self.pad0
			padB = self.pad1
		else:
			padA = self.pad1
			padB = self.pad0

		padA.set_property('xpos', 10)
		padA.set_property('ypos', 10)
		padA.set_property('alpha', 1.0)
		padA.set_property('zorder', 1)
		padA.set_property('width', 0)
		padA.set_property('height', 0)

		padB.set_property('xpos', 310)
		padB.set_property('ypos', 170)
		padB.set_property('alpha', 1.0)
		padB.set_property('zorder', 2)
		padB.set_property('width', 480)
		padB.set_property('height', 270)

		self.state = not self.state
		return True

	def run(self):
		self.pipeline.set_state(Gst.State.PLAYING)
		self.mainloop.run()

	def kill(self):
		self.pipeline.set_state(Gst.State.NULL)
		self.mainloop.quit()

example = Example()
example.run()
