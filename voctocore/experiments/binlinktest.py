#!/usr/bin/python3
import gi, time

gi.require_version('Gst', '1.0')
from gi.repository import GLib, Gst, GObject

GObject.threads_init()
Gst.init(None)

class SrcBin(Gst.Bin):
	def __init__(self):
		super().__init__()
		self.src = Gst.ElementFactory.make('videotestsrc', 'src')
		self.add(self.src)

		self.add_pad(
			Gst.GhostPad.new('src', self.src.get_static_pad('src'))
		)

class SinkBin(Gst.Bin):
	def __init__(self):
		super().__init__()
		self.sink = Gst.ElementFactory.make('autovideosink', 'sink')
		self.add(self.sink)

		self.add_pad(
			Gst.GhostPad.new('sink', self.sink.get_static_pad('sink'))
		)

class MixBin(Gst.Bin):
	def __init__(self):
		super().__init__()
		self.mix = Gst.ElementFactory.make('videomixer', 'src')
		self.add(self.mix)

		self.add_pad(
			Gst.GhostPad.new('src', self.mix.get_static_pad('src'))
		)

	def create_ghostpad(self, pad):
		ghostpad = Gst.GhostPad.new(pad.get_name(), pad)
		self.add_pad(ghostpad)
		return ghostpad

	def add_src(self, src):
		sinkpad = self.mix.get_request_pad('sink_%u')
		sinkpad.set_property('alpha', 0.75)
		srcpad = src.get_static_pad('src')

		# works
		#print(src.link(self.mix)) # True

		# doesn't
		#print(srcpad.link(sinkpad)) # Error => GST_PAD_LINK_WRONG_HIERARCHY

		# but this does
		sinkghostpad = self.create_ghostpad(sinkpad)
		print(srcpad.link(sinkghostpad)) # True

class Example:
	def __init__(self):
		self.mainloop = GObject.MainLoop()
		self.pipeline = Gst.Pipeline()

		self.src = SrcBin()
		self.sink = SinkBin()
		self.mix = MixBin()

		# Add elements to pipeline
		self.pipeline.add(self.src)
		self.pipeline.add(self.sink)
		self.pipeline.add(self.mix)

		self.mix.add_src(self.src)
		self.mix.link(self.sink)

	def run(self):
		self.pipeline.set_state(Gst.State.PLAYING)
		self.mainloop.run()

	def kill(self):
		self.pipeline.set_state(Gst.State.NULL)
		self.mainloop.quit()

example = Example()
example.run()
