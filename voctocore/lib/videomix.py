#!/usr/bin/python3
import logging
from gi.repository import Gst
from enum import Enum

from lib.config import Config

class CompositeModes(Enum):
	fullscreen = 0
	side_by_side_equal = 1

class VideoMix(object):
	log = logging.getLogger('VideoMix')

	mixingPipeline = None

	caps = None
	names = []

	compositeMode = CompositeModes.fullscreen
	sourceA = 0
	sourceB = 1

	def __init__(self):
		self.caps = Config.get('mix', 'videocaps')

		self.names = Config.getlist('mix', 'sources')
		self.log.info('Configuring Mixer for %u Sources', len(self.names))

		pipeline = """
			videomixer name=mix !
			{caps} !
			textoverlay halignment=left valignment=top ypad=175 text=VideoMix !
			timeoverlay halignment=left valignment=top ypad=175 xpad=400 !
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

		self.log.debug('Launching Mixing-Pipeline')
		self.mixingPipeline.set_state(Gst.State.PLAYING)

	def updateMixerState(self):
		if self.compositeMode == CompositeModes.fullscreen:
			self.updateMixerStateFullscreen()

		if self.compositeMode == CompositeModes.side_by_side_equal:
			self.updateMixerStateSideBySideEqual()

	def updateMixerStateFullscreen(self):
		self.log.info('Updating Mixer-State for Fullscreen-Composition')

		noScaleCaps = Gst.Caps.from_string('video/x-raw')

		for idx, name in enumerate(self.names):
			alpha = int(idx == self.sourceA)

			self.log.debug('Setting Mixerpad %u to x/y=0 and alpha=%0.2f', idx, alpha)
			mixerpad = self.mixingPipeline.get_by_name('mix').get_static_pad('sink_%u' % idx)
			mixerpad.set_property('alpha', alpha )
			mixerpad.set_property('xpos', 0)
			mixerpad.set_property('ypos', 0)

			self.log.debug('Resetting Scaler %u to non-scaling', idx)
			capsfilter = self.mixingPipeline.get_by_name('caps_%u' % idx)
			capsfilter.set_property('caps', noScaleCaps)

	def getInputVideoSize(self):
		caps = Gst.Caps.from_string(self.caps)
		struct = caps.get_structure(0)
		_, width = struct.get_int('width')
		_, height = struct.get_int('height')

		return width, height

	def updateMixerStateSideBySideEqual(self):
		self.log.info('Updating Mixer-State for Side-by-side-Equal-Composition')

		width, height = self.getInputVideoSize()
		gutter = int(width / 100)

		self.log.debug('Video-Size parsed as %u/%u, Gutter calculated to %upx', width, height, gutter)

		targetWidth = int((width - gutter) / 2)
		targetHeight = int(targetWidth / width * height)

		ycenter = (height - targetHeight) / 2
		xa = 0
		xb = width - targetWidth

		scaleCaps = Gst.Caps.from_string('video/x-raw,width=%u,height=%u' % (targetWidth, targetHeight))
		noScaleCaps = Gst.Caps.from_string('video/x-raw')

		for idx, name in enumerate(self.names):
			mixerpad = self.mixingPipeline.get_by_name('mix').get_static_pad('sink_%u' % idx)

			if idx == self.sourceA:
				x = xa
				y = ycenter
				caps = scaleCaps
				alpha = 1

				self.log.debug('Setting Mixerpad %u to x/y=%u/%u and alpha=%0.2f', idx, x, y, alpha)
				self.log.debug('Setting Scaler %u to %u/%u', idx, targetWidth, targetHeight)

			elif idx == self.sourceB:
				x = xb
				y = ycenter
				caps = scaleCaps
				alpha = 1

				self.log.debug('Setting Mixerpad %u to x/y=%u/%u and alpha=%0.2f', idx, x, y, alpha)
				self.log.debug('Setting Scaler %u to %u/%u', idx, targetWidth, targetHeight)

			else:
				x = 0
				y = 0
				caps = noScaleCaps
				alpha = 0

				self.log.debug('Setting Mixerpad %u to x/y=%u/%u and alpha=%0.2f', idx, x, y, alpha)
				self.log.debug('Resetting Scaler %u to non-scaling', idx)

			mixerpad.set_property('alpha', alpha)
			mixerpad.set_property('xpos', x)
			mixerpad.set_property('ypos', y)

			capsfilter = self.mixingPipeline.get_by_name('caps_%u' % idx)
			capsfilter.set_property('caps', caps)

	def setVideoSourceA(self, source):
		# swap if required
		if self.sourceB == source:
			self.sourceB = self.sourceA

		self.sourceA = source
		self.updateMixerState()

	def setVideoSourceB(self, source):
		# swap if required
		if self.sourceA == source:
			self.sourceA = self.sourceB

		self.sourceB = source
		self.updateMixerState()

	def setCompositeMode(self, mode):
		self.compositeMode = mode
		self.updateMixerState()
