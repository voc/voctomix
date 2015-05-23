#!/usr/bin/python3
import logging
from gi.repository import Gst

# import library components
from lib.config import Config
from lib.avsource import AVSource
from lib.avrawoutput import AVRawOutput
from lib.avpreviewoutput import AVPreviewOutput
from lib.backgroundsource import BackgroundSource
from lib.videomix import VideoMix
from lib.audiomix import AudioMix

class Pipeline(object):
	"""mixing, streaming and encoding pipeline constuction and control"""

	def __init__(self):
		self.log = logging.getLogger('Pipeline')
		self.log.info('Video-Caps configured to: %s', Config.get('mix', 'videocaps'))
		self.log.info('Audio-Caps configured to: %s', Config.get('mix', 'audiocaps'))

		names = Config.getlist('mix', 'sources')
		if len(names) < 1:
			raise RuntimeException("At least one AVSource must be configured!")

		self.sources = []
		self.mirrors = []
		self.previews = []

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


			if Config.getboolean('previews', 'enabled'):
				port = 14000 + idx
				self.log.info('Creating Preview-Output for AVSource %s at tcp-port %u', name, port)

				preview = AVPreviewOutput('%s_preview' % name, port)
				self.previews.append(preview)


		self.log.info('Creating Videmixer')
		self.vmix = VideoMix()

		self.log.info('Creating Videmixer')
		self.amix = AudioMix()

		port = 16000
		self.bgsrc = BackgroundSource(port)

		port = 11000
		self.log.info('Creating Mixer-Output at tcp-port %u', port)
		self.mixout = AVRawOutput('mix_out', port)

		if Config.getboolean('previews', 'enabled'):
			port = 12000
			self.log.info('Creating Preview-Output for AVSource %s at tcp-port %u', name, port)

			self.mixpreview = AVPreviewOutput('mix_preview', port)
