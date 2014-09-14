#!/usr/bin/python3
import time, logging
from gi.repository import GLib, Gst

from lib.config import Config

class FailVideoSrc(Gst.Bin):
	log = logging.getLogger('FailVideoSrc')
	colors = [
		0xffff0000, # red
		0xff00ff00, # green
		0xff0000ff, # blue
		0xffffff00, # yellow
		0xff00ffff, # cyan
		0xffff00ff, # magenta
		0xffffffff, # white
	]

	def __init__(self, idx, name):
		super().__init__()

		# Create elements
		self.failsrc = Gst.ElementFactory.make('videotestsrc', None)

		# Add elements to Bin
		self.add(self.failsrc)

		# Set properties
		self.failsrc.set_property('foreground-color', self.colors[idx % len(self.colors)])

		# Add Ghost Pads
		self.add_pad(
			Gst.GhostPad.new('src', self.failsrc.get_static_pad('src'))
		)
