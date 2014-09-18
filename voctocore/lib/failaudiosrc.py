#!/usr/bin/python3
import time, logging
from gi.repository import GLib, Gst

from lib.config import Config

class FailAudioSrc(Gst.Bin):
	log = logging.getLogger('FailAudioSrc')

	def __init__(self, idx, name):
		super().__init__()

		# Create elements
		self.failsrc = Gst.ElementFactory.make('audiotestsrc', None)

		# Add elements to Bin
		self.add(self.failsrc)

		# Set properties
		self.failsrc.set_property('freq', 400+idx*50)

		# Add Ghost Pads
		self.add_pad(
			Gst.GhostPad.new('src', self.failsrc.get_static_pad('src'))
		)
