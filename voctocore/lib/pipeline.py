#!/usr/bin/python3
import logging
from gi.repository import Gst

# import controlserver annotation
from lib.controlserver import controlServerEntrypoint

# import library components
from lib.config import Config
from lib.videosrc import VideoSrc
from lib.videosrcmirror import VideoSrcMirror

class Pipeline(object):
	"""mixing, streaming and encoding pipeline constuction and control"""
	log = logging.getLogger('Pipeline')

	vsources = []
	vmirrors = []

	def __init__(self):
		# self.log.debug('Creating A/V-Mixer')
		# self.videomixer = VideoMix()
		# self.add(self.videomixer)

		# self.audiomixer = AudioMix()
		# self.add(self.audiomixer)

		caps = Config.get('mix', 'videocaps')
		self.log.info('Video-Caps configured to: %s', caps)

		for idx, name in enumerate(Config.getlist('sources', 'video')):
			port = 10000 + idx
			self.log.info('Creating Video-Source %s at tcp-port %u', name, port)

			source = VideoSrc(name, port, caps)
			self.vsources.append(source)


			port = 13000 + idx
			self.log.info('Creating Mirror-Output for Video-Source %s at tcp-port %u', name, port)

			mirror = VideoSrcMirror(name, port, caps)
			self.vmirrors.append(mirror)
