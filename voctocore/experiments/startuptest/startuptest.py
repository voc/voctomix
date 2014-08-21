#!/usr/bin/python3

# Example for the startup-problem
#
# The Pipeline will start but the test-image will be still, as long as no
# ShmSink at /tmp/grabber-v is present (run ../test-grabber-src.sh in another shell)
#
# Even though the ShmSrc is not linked to anything and logically not required for
# the videotestsrc or the ximagesink, the whole pipeline won't startup when this element
# fails to start.
#
# once the pipeline is running, it does not matter what happens to the ShmSink on the
# other end, because the TestBin filters all EOS and ERROR Messages coming from the ShmSrc,
# but somehow this is not enough to make the pipeline start in an error-condition..
#

import gi

# import GStreamer and GTK-Helper classes
gi.require_version('Gst', '1.0')
from gi.repository import GLib, Gst, GObject

# init GObject before importing local classes
GObject.threads_init()
Gst.init(None)

from testbin import TestBin

class Example:
	def __init__(self):
		self.mainloop = GObject.MainLoop()
		self.pipeline = Gst.Pipeline()

		self.src = Gst.ElementFactory.make('videotestsrc', None)
		self.sink = Gst.ElementFactory.make('ximagesink', None)

		self.testbin = TestBin()

		# Add elements to pipeline
		self.pipeline.add(self.testbin)
		self.pipeline.add(self.src)
		self.pipeline.add(self.sink)

		self.src.link(self.sink)

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
