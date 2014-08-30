#!/usr/bin/python3
import time, logging
from gi.repository import GLib, Gst

from lib.config import Config

class VideoMix(Gst.Bin):
	log = logging.getLogger('VideoMix')
	mixerpads = []

	def __init__(self):
		super().__init__()

		self.mixer = Gst.ElementFactory.make('videomixer', 'mixer')
		self.scale = Gst.ElementFactory.make('videoscale', 'scale')
		self.conv = Gst.ElementFactory.make('videoconvert', 'conv')

		self.add(self.mixer)
		self.add(self.scale)
		self.add(self.conv)

		caps = Gst.Caps.from_string(Config.get('mix', 'outputcaps'))
		self.mixer.link_filtered(self.scale, caps)
		self.scale.link(self.conv)

		self.add_pad(
			Gst.GhostPad.new('src', self.conv.get_static_pad('src'))
		)

	def request_mixer_pad(self):
		mixerpad = self.mixer.get_request_pad('sink_%u')
		self.mixerpads.append(mixerpad)
		mixerpad.set_property('alpha', 1)

		self.log.info('requested mixerpad %u (named %s)', len(self.mixerpads) - 1, mixerpad.get_name())
		ghostpad = Gst.GhostPad.new(mixerpad.get_name(), mixerpad)
		self.add_pad(ghostpad)
		return ghostpad

	def set_active(self, target):
		self.log.info('setting videosource %u active, disabling other', target)
		for idx, mixerpad in enumerate(self.mixerpads):
			mixerpad.set_property('alpha', int(target == idx))
