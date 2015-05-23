#!/usr/bin/python3
import logging
from gi.repository import Gst
from enum import Enum

from lib.config import Config

class CompositeModes(Enum):
	fullscreen = 0
	side_by_side_equal = 1
	side_by_side_preview = 2

class VideoMix(object):
	log = logging.getLogger('VideoMix')

	def __init__(self):
		self.caps = Config.get('mix', 'videocaps')

		self.names = Config.getlist('mix', 'sources')
		self.log.info('Configuring Mixer for %u Sources', len(self.names))

		pipeline = """
			videomixer name=mix !
			{caps} !
			queue !
			tee name=tee

			tee. ! queue ! intervideosink channel=video_mix_out
		""".format(
			caps=self.caps
		)

		if Config.getboolean('previews', 'enabled'):
			pipeline += """
				tee. ! queue ! intervideosink channel=video_mix_preview
			"""

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

		self.log.debug('Binding Error & End-of-Stream-Signal on Mixing-Pipeline')
		self.mixingPipeline.bus.add_signal_watch()
		self.mixingPipeline.bus.connect("message::eos", self.on_eos)
		self.mixingPipeline.bus.connect("message::error", self.on_error)

		self.log.debug('Initializing Mixer-State')
		self.compositeMode = CompositeModes.fullscreen
		self.sourceA = 0
		self.sourceB = 1
		self.updateMixerState()

		self.log.debug('Launching Mixing-Pipeline')
		self.mixingPipeline.set_state(Gst.State.PLAYING)

	def getInputVideoSize(self):
		caps = Gst.Caps.from_string(self.caps)
		struct = caps.get_structure(0)
		_, width = struct.get_int('width')
		_, height = struct.get_int('height')

		return width, height

	def updateMixerState(self):
		if self.compositeMode == CompositeModes.fullscreen:
			self.updateMixerStateFullscreen()

		elif self.compositeMode == CompositeModes.side_by_side_equal:
			self.updateMixerStateSideBySideEqual()

		elif self.compositeMode == CompositeModes.side_by_side_preview:
			self.updateMixerStateSideBySidePreview()

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

	def updateMixerStateSideBySideEqual(self):
		self.log.info('Updating Mixer-State for Side-by-side-Equal-Composition')

		width, height = self.getInputVideoSize()
		self.log.debug('Video-Size parsed as %ux%u', width, height)

		try:
			gutter = Config.getint('side-by-side-equal', 'gutter')
			self.log.debug('Gutter configured to %u', gutter)
		except:
			gutter = int(width / 100)
			self.log.debug('Gutter calculated to %u', gutter)

		targetWidth = int((width - gutter) / 2)
		targetHeight = int(targetWidth / width * height)

		y = (height - targetHeight) / 2
		xa = 0
		xb = width - targetWidth

		scaleCaps = Gst.Caps.from_string('video/x-raw,width=%u,height=%u' % (targetWidth, targetHeight))
		noScaleCaps = Gst.Caps.from_string('video/x-raw')

		for idx, name in enumerate(self.names):
			mixerpad = self.mixingPipeline.get_by_name('mix').get_static_pad('sink_%u' % idx)
			capsfilter = self.mixingPipeline.get_by_name('caps_%u' % idx)

			if idx == self.sourceA:
				mixerpad.set_property('alpha', 1)
				mixerpad.set_property('xpos', xa)
				mixerpad.set_property('ypos', y)
				capsfilter.set_property('caps', scaleCaps)

				self.log.debug('Setting Mixerpad %u to x/y=%u/%u and alpha=%0.2f', idx, xa, y, 1)
				self.log.debug('Setting Scaler %u to %u/%u', idx, targetWidth, targetHeight)

			elif idx == self.sourceB:
				mixerpad.set_property('alpha', 1)
				mixerpad.set_property('xpos', xb)
				mixerpad.set_property('ypos', y)
				capsfilter.set_property('caps', scaleCaps)

				self.log.debug('Setting Mixerpad %u to x/y=%u/%u and alpha=%0.2f', idx, xb, y, 1)
				self.log.debug('Setting Scaler %u to %u/%u', idx, targetWidth, targetHeight)

			else:
				mixerpad.set_property('alpha', 0)
				mixerpad.set_property('xpos', 0)
				mixerpad.set_property('ypos', 0)
				capsfilter.set_property('caps', noScaleCaps)

				self.log.debug('Setting Mixerpad %u to x/y=%u/%u and alpha=%0.2f', idx, 0, 0, 0)
				self.log.debug('Resetting Scaler %u to non-scaling', idx)

	def updateMixerStateSideBySidePreview(self):
		self.log.info('Updating Mixer-State for Side-by-side-Preview-Composition')

		width, height = self.getInputVideoSize()
		self.log.debug('Video-Size parsed as %ux%u', width, height)

		try:
			asize = [int(i) for i in Config.get('side-by-side-preview', 'asize').split('x', 1)]
			self.log.debug('A-Video-Size configured to %ux%u', asize[0], asize[1])
		except:
			asize = [
				int(width / 1.25), # 80%
				int(height / 1.25) # 80%
			]
			self.log.debug('A-Video-Size calculated to %ux%u', asize[0], asize[1])

		try:
			apos = [int(i) for i in Config.get('side-by-side-preview', 'apos').split('/', 1)]
			self.log.debug('B-Video-Position configured to %u/%u', apos[0], apos[1])
		except:
			apos = [
				int(width / 100), # 1%
				int(width / 100)  # 1%
			]
			self.log.debug('B-Video-Position calculated to %u/%u', apos[0], apos[1])

		try:
			bsize = [int(i) for i in Config.get('side-by-side-preview', 'bsize').split('x', 1)]
			self.log.debug('B-Video-Size configured to %ux%u', bsize[0], bsize[1])
		except:
			bsize = [
				int(width / 4), # 25%
				int(height / 4) # 25%
			]
			self.log.debug('B-Video-Size calculated to %ux%u', bsize[0], bsize[1])

		try:
			bpos = [int(i) for i in Config.get('side-by-side-preview', 'bpos').split('/', 1)]
			self.log.debug('B-Video-Position configured to %u/%u', bpos[0], bpos[1])
		except:
			bpos = [
				width - int(width / 100) - bsize[0],
				height - int(width / 100) - bsize[1]  # 1%
			]
			self.log.debug('B-Video-Position calculated to %u/%u', bpos[0], bpos[1])

		aCaps = Gst.Caps.from_string('video/x-raw,width=%u,height=%u' % tuple(asize))
		bCaps = Gst.Caps.from_string('video/x-raw,width=%u,height=%u' % tuple(bsize))
		noScaleCaps = Gst.Caps.from_string('video/x-raw')

		for idx, name in enumerate(self.names):
			mixerpad = self.mixingPipeline.get_by_name('mix').get_static_pad('sink_%u' % idx)
			capsfilter = self.mixingPipeline.get_by_name('caps_%u' % idx)

			if idx == self.sourceA:
				mixerpad.set_property('alpha', 1)
				mixerpad.set_property('xpos', apos[1])
				mixerpad.set_property('ypos', apos[1])
				mixerpad.set_property('zorder', 0)
				capsfilter.set_property('caps', aCaps)

				self.log.debug('Setting Mixerpad %u to x/y=%u/%u and alpha=%0.2f, zorder=%u', idx, apos[0], apos[1], 1, 1)
				self.log.debug('Setting Scaler %u to %u/%u', idx, asize[0], asize[1])

			elif idx == self.sourceB:
				mixerpad.set_property('alpha', 1)
				mixerpad.set_property('xpos', bpos[0])
				mixerpad.set_property('ypos', bpos[1])
				mixerpad.set_property('zorder', 1)
				capsfilter.set_property('caps', bCaps)

				self.log.debug('Setting Mixerpad %u to x/y=%u/%u, alpha=%0.2f, zorder=%u', idx, bpos[0], bpos[1], 1, 0)
				self.log.debug('Setting Scaler %u to %u/%u', idx, bsize[0], bsize[1])

			else:
				mixerpad.set_property('alpha', 0)
				mixerpad.set_property('xpos', 0)
				mixerpad.set_property('ypos', 0)
				capsfilter.set_property('caps', noScaleCaps)

				self.log.debug('Setting Mixerpad %u to x/y=%u/%u and alpha=%0.2f', idx, 0, 0, 0)
				self.log.debug('Resetting Scaler %u to non-scaling', idx)

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

	def on_eos(self, bus, message):
		self.log.debug('Received End-of-Stream-Signal on Mixing-Pipeline')

	def on_error(self, bus, message):
		self.log.debug('Received Error-Signal on Mixing-Pipeline')
		(error, debug) = message.parse_error()
		self.log.debug('Error-Details: #%u: %s', error.code, debug)
