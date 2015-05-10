#!/usr/bin/python3
import logging
from gi.repository import Gst
from enum import Enum

from lib.config import Config

class ComposteModes(Enum):
	fullscreen = 0

class VideoMix(object):
	log = logging.getLogger('VideoMix')

	mixingPipeline = None

	caps = None
	names = []

	compositeMode = ComposteModes.fullscreen
	sourceA = 0
	sourceB = 1

	def __init__(self):
		self.caps = Config.get('mix', 'videocaps')

		self.names = Config.getlist('sources', 'video')
		self.log.info('Configuring Mixer for %u Sources', len(self.names))

		pipeline = """
			videomixer name=mix !
			{caps} !
			textoverlay text=mixer halignment=left valignment=top ypad=175 !
			intervideosink channel=video_mix
		""".format(
			caps=self.caps
		)

		for idx, name in enumerate(self.names):
			pipeline += """
				intervideosrc channel=video_{name}_mixer !
				{caps} !
				videoscale !
				capsfilter name=caps_{idx} !
				mix.
			""".format(
				name=name,
				caps=self.caps,
				idx=idx
			)

		self.log.debug('Creating Mixing-Pipeline:\n%s', pipeline)
		self.mixingPipeline = Gst.parse_launch(pipeline)

		self.log.debug('Initializing Mixer-State')
		self.updateMixerState()

		self.log.debug('Launching Mixing-Pipeline:\n%s', pipeline)
		self.mixingPipeline.set_state(Gst.State.PLAYING)

	def updateMixerState(self):
		if self.compositeMode == ComposteModes.fullscreen:
			self.updateMixerStateFullscreen()

	def updateMixerStateFullscreen(self):
		self.log.info('Updating Mixer-State for Fullscreen-Composition')
		for idx, name in enumerate(self.names):
			alpha = int(idx == self.sourceA)

			self.log.debug('Setting Mixerpad %u to x/y=0 and alpha=%u', idx, alpha)
			mixerpad = self.mixingPipeline.get_by_name('mix').get_static_pad('sink_%u' % idx)
			mixerpad.set_property('alpha', alpha )
			mixerpad.set_property('xpos', 0)
			mixerpad.set_property('ypos', 0)

			self.log.debug('Resetting Scaler %u to non-scaling', idx)
			capsfilter = self.mixingPipeline.get_by_name('caps_%u' % idx)
			capsfilter.set_property('caps', Gst.Caps.from_string(self.caps))

	def setVideoA(self, source):
		self.sourceA = source
		self.updateMixerState()

	def setVideoB(self, source):
		self.sourceN = source
		self.updateMixerState()
