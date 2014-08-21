#!/usr/bin/python3
import time
from gi.repository import GLib, Gst

class TestBin(Gst.Bin):
	def __init__(self):
		super().__init__()
		self.set_name('testbin')

		# Create elements
		self.shmsrc = Gst.ElementFactory.make('shmsrc', None)

		# Add elements to Bin
		self.add(self.shmsrc)

		self.shmsrc.set_property('socket-path', '/tmp/grabber-v')
		self.shmsrc.set_property('is-live', True)
		self.shmsrc.set_property('do-timestamp', True)

		# Install pad probes
		self.shmsrc.get_static_pad('src').add_probe(Gst.PadProbeType.BLOCK | Gst.PadProbeType.EVENT_DOWNSTREAM, self.event_probe, None)
		self.shmsrc.get_static_pad('src').add_probe(Gst.PadProbeType.BLOCK | Gst.PadProbeType.BUFFER, self.data_probe, None)

	def do_handle_message(self, msg):
		if msg.type == Gst.MessageType.ERROR:
			print("do_handle_message(): dropping error")
			return
		
		print("do_handle_message()", msg.src, msg.type)
		Gst.Bin.do_handle_message(self, msg)

	def event_probe(self, pad, info, ud):
		e = info.get_event()
		if e.type == Gst.EventType.EOS:
			return Gst.PadProbeReturn.DROP

		return Gst.PadProbeReturn.PASS

	def data_probe(self, pad, info, ud):
		self.last_buffer_arrived = time.time()
		return Gst.PadProbeReturn.PASS
