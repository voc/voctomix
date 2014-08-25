#!/usr/bin/python3
import time, logging
from gi.repository import GLib, Gst

from lib.config import Config

class VideoMix(Gst.Bin):
	log = logging.getLogger('VideoMix')
	sinkpads = []

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

	# I don't know how to create a on-request ghost-pad
	def add_source(self, src):
		self.log.info('adding source %s', src.get_name())
		sinkpad = self.mixer.get_request_pad('sink_%u')
		sinkpad.set_property('alpha', 1)
		self.sinkpads.append(sinkpad)

		#srcpad = src.get_compatible_pad(sinkpad, None)
		#srcpad.link(sinkpad)
		src.link(self.mixer) # linking ghost pads

	def set_active(self, target):
		self.log.info('setting source #%u active', target)
		for idx, sinkpad in enumerate(self.sinkpads):
			sinkpad.set_property('alpha', int(target == idx))
