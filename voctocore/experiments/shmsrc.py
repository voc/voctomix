#!/usr/bin/python3
from gi.repository import GObject, Gst

class ShmSrc(Gst.Bin):
	def __init__(self, socket, caps):
		super().__init__()

		# Create elements
		self.shmsrc = Gst.ElementFactory.make('shmsrc', None)
		self.caps1 = Gst.ElementFactory.make('capsfilter', None)
		self.caps2 = Gst.ElementFactory.make('capsfilter', None)
		self.switch = Gst.ElementFactory.make('input-selector', None)
		self.secondsrc = Gst.ElementFactory.make('videotestsrc', None)

		# Add elements to Bin
		self.add(self.shmsrc)
		self.add(self.caps1)
		self.add(self.caps2)
		self.add(self.switch)
		self.add(self.secondsrc)

		# Get Switcher-Pads
		self.firstpad = self.switch.get_request_pad('sink_%u')
		self.secondpad = self.switch.get_request_pad('sink_%u')

		# Set properties
		self.shmsrc.set_property('socket-path', socket)
		self.shmsrc.set_property('is-live', True)
		self.shmsrc.set_property('do-timestamp', True)
		self.caps1.set_property('caps', caps)
		self.caps2.set_property('caps', caps)
		self.switch.set_property('active-pad', self.firstpad)
		self.secondsrc.set_property('pattern', 'snow')

		# Link elements
		self.shmsrc.link(self.caps1)
		self.caps1.get_static_pad('src').link(self.firstpad)

		self.secondsrc.link(self.caps2)
		self.caps2.get_static_pad('src').link(self.secondpad)

		# Install pad probes
		self.shmsrc.get_static_pad('src').add_probe(Gst.PadProbeType.BLOCK | Gst.PadProbeType.EVENT_DOWNSTREAM, self.event_probe, None)
		self.shmsrc.get_static_pad('src').add_probe(Gst.PadProbeType.IDLE | Gst.PadProbeType.DATA_DOWNSTREAM, self.data_probe, None)

		# Add Ghost Pads
		self.add_pad(
			Gst.GhostPad.new('sink', self.switch.get_static_pad('src'))
		)

	def event_probe(self, pad, info, ud):
		e = info.get_event()
		print("event_probe", e.type)
		if e.type == Gst.EventType.EOS:
			print("shmsrc reported EOS - switching to failover")
			self.switch.set_property('active-pad', self.secondpad)
			return Gst.PadProbeReturn.DROP
		return Gst.PadProbeReturn.PASS

	def data_probe(self, pad, info, ud):
		print("shmsrc sends data - switching to shmsrc")
		# todo: add a timeout of 2*framerate (ie 2*1/25 seconds)
		return Gst.PadProbeReturn.PASS
