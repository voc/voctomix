#!/usr/bin/python3
import logging
from gi.repository import Gst

# import library components
from lib.config import Config
from lib.avsource import AVSource
from lib.avrawoutput import AVRawOutput

class Pipeline(object):
	"""mixing, streaming and encoding pipeline constuction and control"""
	log = logging.getLogger('Pipeline')

	sources = []
	mirrors = []

	def __init__(self):
		self.log.info('Video-Caps configured to: %s', Config.get('mix', 'videocaps'))
		self.log.info('Audio-Caps configured to: %s', Config.get('mix', 'audiocaps'))

		names = Config.getlist('mix', 'sources')
		if len(names) < 1:
			raise RuntimeException("At least one AVSource must be configured!")

		self.log.info('Creating %u Creating AVSources: %s', len(names), names)
		for idx, name in enumerate(names):
			port = 10000 + idx
			self.log.info('Creating AVSource %s at tcp-port %u', name, port)

			source = AVSource(name, port)
			self.sources.append(source)


			port = 13000 + idx
			self.log.info('Creating Mirror-Output for AVSource %s at tcp-port %u', name, port)

			mirror = AVRawOutput('%s_mirror' % name, port)
			self.mirrors.append(mirror)
