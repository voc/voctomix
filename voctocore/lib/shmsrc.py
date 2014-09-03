#!/usr/bin/python3
import time, logging
from gi.repository import GLib, Gst

from lib.config import Config

class FailsafeShmSrc(Gst.Bin):
	log = logging.getLogger('FailsafeShmSrc')
	last_buffer_arrived = 0
	last_restart_retry = 0
	is_in_failstate = True

	def __init__(self, socket):
		super().__init__()

		caps = Gst.Caps.from_string(Config.get('sources', 'videocaps'))
		self.log.debug('parsing videocaps from config: %s', caps.to_string())

		# Create elements
		self.shmsrc = Gst.ElementFactory.make('shmsrc', None)
		self.identity1 = Gst.ElementFactory.make('identity', None)
		self.identity2 = Gst.ElementFactory.make('identity', None)
		self.switch = Gst.ElementFactory.make('input-selector', None)
		self.failsrc = Gst.ElementFactory.make('videotestsrc', None)

		if not self.shmsrc or not self.identity1 or not self.identity2 or not self.switch or not self.failsrc:
			self.log.error('could not create elements')

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
		self.identity2.set_property('sync', True)
		self.switch.set_property('active-pad', self.failpad)

		# Link elements
		self.shmsrc.link_filtered(self.identity1, caps)
		self.identity1.get_static_pad('src').link(self.goodpad)

		self.failsrc.link_filtered(self.identity2, caps)
		self.identity2.get_static_pad('src').link(self.failpad)

		# Install pad probes
		self.shmsrc.get_static_pad('src').add_probe(Gst.PadProbeType.BLOCK | Gst.PadProbeType.EVENT_DOWNSTREAM, self.event_probe, None)
		self.shmsrc.get_static_pad('src').add_probe(Gst.PadProbeType.BLOCK | Gst.PadProbeType.BUFFER, self.data_probe, None)

		# Install Watchdog
		GLib.timeout_add(250, self.watchdog)

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
