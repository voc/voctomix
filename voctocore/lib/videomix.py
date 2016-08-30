import logging
from gi.repository import Gst
from enum import Enum, unique

from lib.config import Config
from lib.clock import Clock

class PadState(object):
	def __init__(self):
		self.reset()

	def reset(self):
		self.alpha = 0.0
		self.xpos, self.ypos = 0, 0
		self.ypos = 0
		self.zorder = 1
		self.width, self.height = VideoMix.getVideoSize()

class VideoMix(object):
	log = logging.getLogger('VideoMix')

	def getVideoSize():
		capsstr = Config.get('mix', 'videocaps')
		caps = Gst.Caps.from_string(capsstr)
		struct = caps.get_structure(0)
		_, width = struct.get_int('width')
		_, height = struct.get_int('height')

		return width, height

	def __init__(self):
		self.caps = Config.get('mix', 'videocaps')

		self.width, self.height = VideoMix.getVideoSize()
		self.log.debug('Video-Size parsed as %ux%u', self.width, self.height)

		self.names = Config.getlist('mix', 'sources')
		self.log.info('Configuring Mixer for %u Sources', len(self.names))

		pipeline = """
			compositor name=mix !
			{caps} !
			identity name=sig !
			queue !
			tee name=tee

			intervideosrc channel=video_background !
			{caps} !
			mix.

			tee. ! queue ! intervideosink channel=video_mix_out
		""".format(
			caps=self.caps
		)

		if Config.getboolean('previews', 'enabled'):
			pipeline += """
				tee. ! queue ! intervideosink channel=video_mix_preview
			"""

		if Config.getboolean('stream-blanker', 'enabled'):
			pipeline += """
				tee. ! queue ! intervideosink channel=video_mix_streamblanker
			"""

		for idx, name in enumerate(self.names):
			pipeline += """
				intervideosrc channel=video_{name}_mixer !
				{caps} !
				mix.
			""".format(
				name=name,
				caps=self.caps,
				idx=idx
			)

		self.log.debug('Creating Mixing-Pipeline:\n%s', pipeline)
		self.mixingPipeline = Gst.parse_launch(pipeline)
		self.mixingPipeline.use_clock(Clock)

		self.log.debug('Binding Error & End-of-Stream-Signal on Mixing-Pipeline')
		self.mixingPipeline.bus.add_signal_watch()
		self.mixingPipeline.bus.connect("message::eos", self.on_eos)
		self.mixingPipeline.bus.connect("message::error", self.on_error)

		self.log.debug('Binding Handoff-Handler for Synchronus mixer manipulation')
		sig = self.mixingPipeline.get_by_name('sig')
		sig.connect('handoff', self.on_handoff)

		self.padStateDirty = False
		self.padState = list()
		for idx, name in enumerate(self.names):
			self.padState.append(PadState())

		self.scenes = Config.get_prefixed_sections('scene.')
		if len(self.scenes) == 0:
			raise RuntimeError("At least one Scene must be configured!")

		self.log.info('Initializing Mixer-State to first scene "%s"', self.scenes[0])
		self.scene = self.scenes[0]
		self.setScene(self.scene)

		bgMixerpad = self.mixingPipeline.get_by_name('mix').get_static_pad('sink_0')
		bgMixerpad.set_property('zorder', 0)

		self.log.debug('Launching Mixing-Pipeline')
		self.mixingPipeline.set_state(Gst.State.PLAYING)

	def setScene(self, scene):
		section = 'scene.' + scene
		print(section)
		if not Config.has_section(section):
			raise RuntimeError("Invalid scene: %s" % scene)

		self.scene = scene
		aspect = self.width / self.height

		scope = {}
		scope['aspect'] = aspect
		scope['w'], scope['h'] = self.width, self.height

		if Config.has_section('scenes'):
			for k, v in Config.items('scenes'):
				scope[k] = eval(v, {}, scope)

		self.log.debug('Evaluating Scene-Expressions in the following scope: %s', scope)

		for idx, source in enumerate(self.names):
			self.padState[idx].reset()

			if Config.has_option(section, source+'.alpha'):
				alpha = Config.get(section, source+'.alpha')

				self.padState[idx].alpha = float(eval(alpha, {}, dict(scope)))

			if Config.has_option(section, source+'.zorder'):
				zorder = Config.get(section, source+'.zorder')
				self.padState[idx].zorder = int(eval(zorder, {}, dict(scope)))


			width, height = None, None
			if Config.has_option(section, source+'.size'):
				width, height = Config.get(section, source+'.size').split(',')

			if Config.has_option(section, source+'.width'):
				width = Config.get(section, source+'.width')

			if Config.has_option(section, source+'.height'):
				height = Config.get(section, source+'.height')

			if width:
				self.padState[idx].width = int(eval(width, {}, dict(scope)))

				if not height:
					self.padState[idx].height = self.padState[idx].width / aspect

			if height:
				self.padState[idx].height = int(eval(height, {}, dict(scope)))

				if not width:
					self.padState[idx].width = self.padState[idx].height * aspect


			left, top = None, None
			if Config.has_option(section, source+'.topleft'):
				top, left = Config.get(section, source+'.topleft').split(',')

			if Config.has_option(section, source+'.left'):
				left = Config.get(section, source+'.left')

			if Config.has_option(section, source+'.top'):
				top = Config.get(section, source+'.top')

			if left:
				self.padState[idx].xpos = int(eval(left, {}, dict(scope)))

			if top:
				self.padState[idx].ypos = int(eval(top, {}, dict(scope)))


			right, bottom = None, None
			if Config.has_option(section, source+'.bottomright'):
				bottom, right = Config.get(section, source+'.bottomright').split(',')

			if Config.has_option(section, source+'.right'):
				right = Config.get(section, source+'.right')

			if Config.has_option(section, source+'.bottom'):
				bottom = Config.get(section, source+'.bottom')

			if right:
				right = int(eval(right, {}, dict(scope)))
				if left:
					if width:
						# right, left & width. overspecified
						self.log.warn('scene %s overspecified source %s xpos by providinf, left, width and right. ignoring right', scene, source)
					else:
						# right & left but no width. calculate width
						self.padState[idx].width = self.width - right - self.padState[idx].xpos
						self.log.debug('left & right specified, calculating width=%u', self.padState[idx].width)

						if not height:
							self.padState[idx].height = self.padState[idx].width / aspect
							self.log.debug('height not specified, calculating height=%u to fit aspect ratio', self.padState[idx].height)

				else:
					# right no left. calulate xpos
					self.padState[idx].xpos = self.width - self.padState[idx].width - right
					self.log.debug('right and width specified, calculating xpos=%u', self.padState[idx].xpos)



			if bottom:
				bottom = int(eval(bottom, {}, dict(scope)))
				if top:
					if height:
						# bottom, top & height. overspecified
						self.log.warn('scene %s overspecified source %s ypos by providinf, top, height and bottom. ignoring bottom', scene, source)
					else:
						# bottom & top but no height. calculate height
						self.padState[idx].height = self.height - bottom - self.padState[idx].ypos
						self.log.debug('top & bottom specified, calculating height=%u', self.padState[idx].height)

						if not width:
							self.padState[idx].width = self.padState[idx].height * aspect
							self.log.debug('width not specified, calculating width=%u to fit aspect ratio', self.padState[idx].width)

				else:
					# bottom no top. calulate ypos
					self.padState[idx].ypos = self.height - self.padState[idx].height - bottom
					self.log.debug('bottom and height specified, calculating ypos=%u', self.padState[idx].ypos)


		self.applyMixerState()



	def getScene(self):
		return self.scene


	def applyMixerState(self):
		for idx, state in enumerate(self.padState):
			# mixerpad 0 = background
			mixerpad = self.mixingPipeline.get_by_name('mix').get_static_pad('sink_%u' % (idx+1))

			self.log.debug('Reconfiguring Mixerpad %u to x/y=%u/%u, w/h=%u/%u alpha=%0.2f, zorder=%u', \
				idx, state.xpos, state.ypos, state.width, state.height, state.alpha, state.zorder)
			mixerpad.set_property('xpos', state.xpos)
			mixerpad.set_property('ypos', state.ypos)
			mixerpad.set_property('width', state.width)
			mixerpad.set_property('height', state.height)
			mixerpad.set_property('alpha', state.alpha)
			mixerpad.set_property('zorder', state.zorder)

	def on_handoff(self, object, buffer):
		if self.padStateDirty:
			self.padStateDirty = False
			self.log.debug('[Streaming-Thread]: Pad-State is Dirty, applying new Mixer-State')
			self.applyMixerState()

	def on_eos(self, bus, message):
		self.log.debug('Received End-of-Stream-Signal on Mixing-Pipeline')

	def on_error(self, bus, message):
		self.log.debug('Received Error-Signal on Mixing-Pipeline')
		(error, debug) = message.parse_error()
		self.log.debug('Error-Details: #%u: %s', error.code, debug)
