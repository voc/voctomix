#!/usr/bin/python3
import logging
from gi.repository import Gst

from lib.config import Config

class VideoMix(object):
	log = logging.getLogger('VideoMix')

	def __init__(self):
		caps = Config.get('mix', 'videocaps')

		names = Config.getlist('sources', 'video')
		self.log.info('Configuring Mixer for %u Sources', len(names))
		#for idx, name in enumerate():
