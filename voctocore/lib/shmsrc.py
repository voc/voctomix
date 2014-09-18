#!/usr/bin/python3
import time, logging
from gi.repository import GLib, Gst

from lib.config import Config

class FailsafeShmSrc(Gst.Bin):
	log = logging.getLogger('FailsafeShmSrc')
	last_buffer_arrived = 0
	last_restart_retry = 0
	is_in_failstate = True

	def __init__(self, socket, caps, failsrc):
		super().__init__()

		# Create elements
		self.shmsrc = Gst.ElementFactory.make('shmsrc', None)
		self.depay = Gst.ElementFactory.make('gdpdepay', None)
		self.capsfilter = Gst.ElementFactory.make('capsfilter', None)
		self.failsrcsyncer = Gst.ElementFactory.make('identity', None)
		self.switch = Gst.ElementFactory.make('input-selector', None)
		self.failsrc = failsrc
		self.capsstr = caps.to_string()

		if not self.shmsrc or not self.capsfilter or not self.failsrcsyncer or not self.switch or not self.failsrc:
			self.log.error('could not create elements')

		# Add elements to Bin
		self.add(self.shmsrc)
		self.add(self.depay)
		self.add(self.capsfilter)
		self.add(self.failsrcsyncer)
		self.add(self.switch)
		self.add(self.failsrc)

		# Get Switcher-Pads
		self.goodpad = self.switch.get_request_pad('sink_%u')
		self.failpad = self.switch.get_request_pad('sink_%u')

		# Set properties
		self.shmsrc.set_property('socket-path', socket)
		self.shmsrc.link(self.depay)
		self.switch.set_property('active-pad', self.failpad)
		self.failsrcsyncer.set_property('sync', True)
		self.capsfilter.set_property('caps', caps)

		# Link elements
		self.depay.link(self.capsfilter)
		self.capsfilter.get_static_pad('src').link(self.goodpad)

		self.failsrc.link_filtered(self.failsrcsyncer, caps)
		self.failsrcsyncer.get_static_pad('src').link(self.failpad)

		# Install pad probes
		self.shmsrc.get_static_pad('src').add_probe(Gst.PadProbeType.BLOCK | Gst.PadProbeType.EVENT_DOWNSTREAM, self.event_probe, None)
		self.shmsrc.get_static_pad('src').add_probe(Gst.PadProbeType.BLOCK | Gst.PadProbeType.BUFFER, self.data_probe, None)

		# Install Watchdog
		if self.capsstr.startswith('audio'):
			timeoutms = 1000
		else:
			timeoutms = 250

		GLib.timeout_add(timeoutms, self.watchdog)

		# Add Ghost Pads
		self.add_pad(
			Gst.GhostPad.new('src', self.switch.get_static_pad('src'))
		)

	def do_handle_message(self, msg):
		if msg.type == Gst.MessageType.ERROR and msg.src == self.shmsrc:
			(err, debug) = msg.parse_error()
			self.log.warning('received error-message from ShmSrc, dropping: %s', err)
			self.log.debug('    debug-info from shmsrc: %s', debug)
		else:
			Gst.Bin.do_handle_message(self, msg)

	def event_probe(self, pad, info, ud):
		e = info.get_event()
		if e.type == Gst.EventType.EOS:
			self.log.warning('received EOS-event on event-probe, dropping')
			self.switch_to_failstate()
			return Gst.PadProbeReturn.DROP
		
		return Gst.PadProbeReturn.PASS

	def data_probe(self, pad, info, ud):
		self.last_buffer_arrived = time.time()
		self.switch_to_goodstate()
		return Gst.PadProbeReturn.PASS

	def watchdog(self):
		t = time.time()
		if self.last_buffer_arrived + 0.1 < t:
			self.log.warning('watchdog encountered a timeout')
			self.switch_to_failstate()
		
		if self.is_in_failstate and self.last_restart_retry + 1 < t:
			self.last_restart_retry = t
			self.restart()
		
		return True
	
	def restart(self):
		self.log.warning('restarting ShmSrc')
		self.shmsrc.set_state(Gst.State.NULL)
		self.shmsrc.set_base_time(self.get_parent().get_base_time())
		self.shmsrc.set_state(Gst.State.PLAYING)
	
	def switch_to_goodstate(self):
		if not self.is_in_failstate:
			return
		
		self.log.warning('switching output to goodstate')
		self.is_in_failstate = False
		self.switch.set_property('active-pad', self.goodpad)
	
	def switch_to_failstate(self):
		if self.is_in_failstate:
			return
		
		self.log.warning('switching output to failstate')
		self.is_in_failstate = True
		self.switch.set_property('active-pad', self.failpad)
