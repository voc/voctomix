#!/usr/bin/python3
import time
from gi.repository import GLib, Gst

class ShmSrc(Gst.Bin):
	last_buffer_arrived = 0
	is_in_failstate = True

	def __init__(self, socket, caps):
		super().__init__()

		# Create elements
		self.shmsrc = Gst.ElementFactory.make('shmsrc', None)
		self.identity1 = Gst.ElementFactory.make('identity', None)
		self.identity2 = Gst.ElementFactory.make('identity', None)
		self.switch = Gst.ElementFactory.make('input-selector', None)
		self.failsrc = Gst.ElementFactory.make('videotestsrc', None)

		# Add elements to Bin
		self.add(self.shmsrc)
		self.add(self.identity1)
		self.add(self.identity2)
		self.add(self.switch)
		self.add(self.failsrc)

		# Get Switcher-Pads
		self.goodpad = self.switch.get_request_pad('sink_%u')
		self.failpad = self.switch.get_request_pad('sink_%u')

		# Set properties
		self.shmsrc.set_property('socket-path', socket)
		self.shmsrc.set_property('is-live', True)
		self.shmsrc.set_property('do-timestamp', True)
		#self.identity1.set_property('sync', True)
		self.identity2.set_property('sync', True)
		self.switch.set_property('active-pad', self.failpad)
		self.failsrc.set_property('pattern', 'snow')

		# Link elements
		self.shmsrc.link_filtered(self.identity1, caps)
		self.identity1.get_static_pad('src').link(self.goodpad)

		self.failsrc.link_filtered(self.identity2, caps)
		self.identity2.get_static_pad('src').link(self.failpad)

		# Install pad probes
		self.shmsrc.get_static_pad('src').add_probe(Gst.PadProbeType.BLOCK | Gst.PadProbeType.EVENT_DOWNSTREAM, self.event_probe, None)
		self.shmsrc.get_static_pad('src').add_probe(Gst.PadProbeType.BLOCK | Gst.PadProbeType.BUFFER, self.data_probe, None)

		# Install Watchdog
		GLib.timeout_add(500, self.watchdog)

		# Add Ghost Pads
		self.add_pad(
			Gst.GhostPad.new('sink', self.switch.get_static_pad('src'))
		)

	def do_handle_message(self, msg):
		if msg.type == Gst.MessageType.ERROR:
			print("do_handle_message(): dropping error")
			return
		
		print("do_handle_message()", msg.src, msg.type)
		Gst.Bin.do_handle_message(self, msg)

	def event_probe(self, pad, info, ud):
		e = info.get_event()
		if e.type == Gst.EventType.EOS:
			self.switch_to_failstate()
			return Gst.PadProbeReturn.DROP
		
		return Gst.PadProbeReturn.PASS


	def data_probe(self, pad, info, ud):
		self.last_buffer_arrived = time.time()
		self.switch_to_goodstate()
		return Gst.PadProbeReturn.PASS

	def watchdog(self):
		if self.last_buffer_arrived + 0.1 < time.time():
			print("watchdog()::timeout")
			self.switch_to_failstate()
		
		if self.last_buffer_arrived + 3 < time.time() and round(time.time() % 3) == 0:
			print("watchdog()::restart")
			self.restart()
		
		return True
	
	def restart(self):
		self.shmsrc.set_state(Gst.State.NULL)
		self.shmsrc.set_state(Gst.State.PLAYING)
	
	def switch_to_goodstate(self):
		if not self.is_in_failstate:
			return
		
		print("switch_to_goodstate()")
		self.is_in_failstate = False
		self.switch.set_property('active-pad', self.goodpad)
	
	def switch_to_failstate(self):
		if self.is_in_failstate:
			return
		
		print("switch_to_failstate()")
		self.is_in_failstate = True
		self.switch.set_property('active-pad', self.failpad)
