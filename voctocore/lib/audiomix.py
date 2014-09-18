#!/usr/bin/python3
import time, logging
from gi.repository import GLib, Gst

from lib.config import Config

class AudioMix(Gst.Bin):
	log = logging.getLogger('AudioMix')
	mixerpads = []

	def __init__(self):
		super().__init__()

		self.switch = Gst.ElementFactory.make('input-selector', 'switch')

		self.add(self.switch)
		self.switch.set_property('sync-streams', True)
		self.switch.set_property('sync-mode', 1) #GST_INPUT_SELECTOR_SYNC_MODE_CLOCK
		self.switch.set_property('cache-buffers', True)

		self.add_pad(
			Gst.GhostPad.new('src', self.switch.get_static_pad('src'))
		)

	def request_mixer_pad(self):
		mixerpad = self.switch.get_request_pad('sink_%u')
		self.mixerpads.append(mixerpad)

		self.log.info('requested mixerpad %u (named %s)', len(self.mixerpads) - 1, mixerpad.get_name())
		ghostpad = Gst.GhostPad.new(mixerpad.get_name(), mixerpad)
		self.add_pad(ghostpad)
		return ghostpad

	def set_active(self, target):
		self.log.info('switching to audiosource %u', target)
		self.switch.set_property('active-pad', self.mixerpads[target])
