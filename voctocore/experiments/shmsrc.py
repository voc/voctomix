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
		self.shmsrc.get_static_pad('src').add_probe(Gst.PadProbeType.BLOCK | Gst.PadProbeType.EVENT_DOWNSTREAM, self.event_probe, None)
		self.shmsrc.get_static_pad('src').add_probe(Gst.PadProbeType.IDLE | Gst.PadProbeType.DATA_DOWNSTREAM, self.data_probe, None)

		# Add Ghost Pads
		self.add_pad(
			Gst.GhostPad.new('sink', self.caps.get_static_pad('src'))
		)

	def event_probe(self, pad, info, ud):
		e = info.get_event()
		print("event_probe", e.type)
		if e.type == Gst.EventType.EOS:
			print("shmsrc reported EOS - switching to failover")
			return Gst.PadProbeReturn.DROP
		return Gst.PadProbeReturn.PASS

	def data_probe(self, pad, info, ud):
		print("shmsrc sends data - switching to shmsrc")
		return Gst.PadProbeReturn.PASS
