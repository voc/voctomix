#!/usr/bin/python3
import logging
from gi.repository import Gst

# import controlserver annotation
from lib.controlserver import controlServerEntrypoint

# import library components
from lib.config import Config
from lib.video.src import VideoSrc
from lib.video.rawoutput import VideoRawOutput
from lib.video.mix import VideoMix

class Pipeline(object):
	"""mixing, streaming and encoding pipeline constuction and control"""
	log = logging.getLogger('Pipeline')

	vsources = []
	vmirrors = []
	vpreviews = []
	vmixer = None
	vmixerout = None

	def __init__(self):
		self.initVideo()

	def initVideo(self):
		caps = Config.get('mix', 'videocaps')
		self.log.info('Video-Caps configured to: %s', caps)

		names = Config.getlist('sources', 'video')
		if len(names) < 1:
			raise RuntimeException("At least one Video-Source must be configured!")

		for idx, name in enumerate(names):
			port = 10000 + idx
			self.log.info('Creating Video-Source %s at tcp-port %u', name, port)

			source = VideoSrc(name, port, caps)
			self.vsources.append(source)


			port = 13000 + idx
			self.log.info('Creating Mirror-Output for Video-Source %s at tcp-port %u', name, port)

			mirror = VideoRawOutput('video_%s_mirror' % name, port, caps)
			self.vmirrors.append(mirror)

		self.log.debug('Creating Video-Mixer')
		self.videomixer = VideoMix()

		port = 11000
		self.log.debug('Creating Video-Mixer-Output at tcp-port %u', port)
		self.vmixerout = VideoRawOutput('video_mix', port, caps)
