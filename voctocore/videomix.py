import sys, inspect
from pprint import pprint
from gi.repository import GLib, Gst

class Videomix:
	decoder = []
	mixerpads = []

	def __init__(self):
		self.pipeline = Gst.Pipeline()

		self.videomixer = Gst.ElementFactory.make('videomixer', 'videomixer')
		self.pipeline.add(self.videomixer)

		for uri in ("http://video.blendertestbuilds.de/download.blender.org/ED/ED_1280.avi", "http://download.blender.org/durian/trailer/sintel_trailer-720p.mp4",):
			decoder = Gst.ElementFactory.make('uridecodebin', 'uridecoder('+uri+')')
			decoder.set_property("uri", uri)
			decoder.connect("pad-added", self.OnDynamicPad)
			self.pipeline.add(decoder)
			self.decoder.append(decoder)

		self.monitorvideosink = Gst.ElementFactory.make('autovideosink', 'monitorvideosink')
		self.pipeline.add(self.monitorvideosink)
		self.videomixer.link(self.monitorvideosink)

		self.monitoraudiosink = Gst.ElementFactory.make('autoaudiosink', 'monitoraudiosink')
		self.pipeline.add(self.monitoraudiosink)

		self.pipeline.set_state(Gst.State.PLAYING)

		GLib.io_add_watch(sys.stdin, GLib.IO_IN, self.Input)

	def Input(self, fd, condition):
		if condition == GLib.IO_IN:
			char = fd.readline()
			try:
				i = int(char.rstrip())
				print("settinh pad {0} to alpha=1".format(i))
				self.mixerpads[i].set_property('alpha', 1)
				for idx, pad in enumerate(self.mixerpads):
					if idx != i:
						print("settinh pad {0} to alpha=0".format(idx))
						pad.set_property('alpha', 0)
			except:
				pass

			return True
		else:
			return False

	def OnDynamicPad(self, uridecodebin, src_pad):
		caps = src_pad.query_caps(None).to_string()
		srcname = uridecodebin.get_name()
		print("{0}-source of {1} online".format(caps.split(',')[0], srcname))

		if caps.startswith('audio/'):
			sinkpad = self.monitoraudiosink.get_static_pad("sink")

			# link the first audio-stream and be done
			if not sinkpad.is_linked():
				src_pad.link(sinkpad)

		else:
			sinkpad = Gst.Element.get_request_pad(self.videomixer, "sink_%u")
			src_pad.link(sinkpad)
			self.mixerpads.append(sinkpad)
			print('add', sinkpad)
			sinkpad.set_property('alpha', 0.7)

