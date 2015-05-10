#!/usr/bin/python3
import logging
from gi.repository import Gst

# import library components
from lib.config import Config
from lib.video.src import VideoSrc
from lib.video.rawoutput import VideoRawOutput
from lib.video.mix import VideoMix

from lib.audio.src import AudioSrc
from lib.audio.rawoutput import AudioRawOutput
from lib.audio.mix import AudioMix

class Pipeline(object):
	"""mixing, streaming and encoding pipeline constuction and control"""
	log = logging.getLogger('Pipeline')

	vsources = []
	vmirrors = []
	vpreviews = []
	vmixer = None
	vmixerout = None

	asources = []
	amirrors = []
	apreviews = []
	amixer = None
	amixerout = None

	def __init__(self):
		self.log.debug('creating Video-Pipeline')
		self.initVideo()

		self.log.debug('creating Audio-Pipeline')
		self.initAudio()

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
		self.vmixer = VideoMix()

		port = 11000
		self.log.debug('Creating Video-Mixer-Output at tcp-port %u', port)
		self.vmixerout = VideoRawOutput('video_mix', port, caps)

	def initAudio(self):
		caps = Config.get('mix', 'audiocaps')
		self.log.info('Audio-Caps configured to: %s', caps)

		names = Config.getlist('sources', 'audio')
		if len(names) < 1:
			raise RuntimeException("At least one Audio-Source must be configured!")

		for idx, name in enumerate(names):
			port = 20000 + idx
			self.log.info('Creating Audio-Source %s at tcp-port %u', name, port)

			source = AudioSrc(name, port, caps)
			self.asources.append(source)


			port = 23000 + idx
			self.log.info('Creating Mirror-Output for Audio-Source %s at tcp-port %u', name, port)

			mirror = AudioRawOutput('audio_%s_mirror' % name, port, caps)
			self.amirrors.append(mirror)
