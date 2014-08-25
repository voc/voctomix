#!/usr/bin/python3
import time, logging
from gi.repository import GLib, Gst

from lib.config import Config

class TimesTwoDistributor(Gst.Bin):
	log = logging.getLogger('TimesTwoDistributor')

	def __init__(self):
		super().__init__()

		self.tee = Gst.ElementFactory.make('tee', None)
		self.queue_a = Gst.ElementFactory.make('queue', 'queue-a')
		self.queue_b = Gst.ElementFactory.make('queue', 'queue-b')
		
		self.add(self.tee)
		self.add(self.queue_a)
		self.add(self.queue_b)

		self.tee.link(self.queue_a)
		self.tee.link(self.queue_b)

		# Add Ghost Pads
		self.add_pad(
			Gst.GhostPad.new('sink', self.tee.get_static_pad('sink'))
		)
		self.add_pad(
			Gst.GhostPad.new('src_a', self.queue_a.get_static_pad('src'))
		)
		self.add_pad(
			Gst.GhostPad.new('src_b', self.queue_b.get_static_pad('src'))
		)
