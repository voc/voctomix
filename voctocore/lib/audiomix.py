#!/usr/bin/python3
import logging
from gi.repository import Gst
from enum import Enum

from lib.config import Config

class AudioMix(object):
	log = logging.getLogger('AudioMix')

	mixingPipeline = None

	caps = None
	names = []

	selectedSource = 0

	def __init__(self):
		self.caps = Config.get('mix', 'audiocaps')

		pipeline = """
			interaudiosrc channel=audio_cam1_mixer !
			{caps} !
			queue !
			interaudiosink channel=audio_mix
		""".format(
			caps=self.caps
		)

		self.log.debug('Creating Mixing-Pipeline:\n%s', pipeline)
		self.mixingPipeline = Gst.parse_launch(pipeline)
		self.mixingPipeline.set_state(Gst.State.PLAYING)
