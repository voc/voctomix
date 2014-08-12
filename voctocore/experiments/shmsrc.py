#!/usr/bin/python3
from gi.repository import GObject, Gst

class ShmSrc(Gst.Bin):
	def __init__(self, socket, caps):
		super().__init__()

		# Create elements
		self.shmsrc = Gst.ElementFactory.make('shmsrc', None)
		self.caps = Gst.ElementFactory.make('capsfilter', None)

		# Add elements to Bin
		self.add(self.shmsrc)
		self.add(self.caps)

		# Set properties
		self.shmsrc.set_property('socket-path', socket)
		self.shmsrc.set_property('is-live', True)
		self.shmsrc.set_property('do-timestamp', True)

		self.caps.set_property('caps', caps)
		self.shmsrc.link(self.caps)
		self.shmsrc.get_static_pad('src').add_probe(Gst.PadProbeType.BLOCK | Gst.PadProbeType.EVENT_BOTH, self.event_probe, None)

		# Add Ghost Pads
		self.add_pad(
			Gst.GhostPad.new('sink', self.caps.get_static_pad('src'))
		)

	def event_probe(self, pad, info, ud):
		print("event_probe")
