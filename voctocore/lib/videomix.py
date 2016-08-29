import logging
from gi.repository import Gst
from enum import Enum, unique

from lib.config import Config
from lib.clock import Clock

class PadState(object):
	def __init__(self):
		self.reset()

	def reset(self):
		self.alpha = 1.0
		self.xpos = 0
		self.ypos = 0
		self.zorder = 1
		self.width = 0
		self.height = 0

class VideoMix(object):
	log = logging.getLogger('VideoMix')

	def __init__(self):
		self.caps = Config.get('mix', 'videocaps')

		self.width, self.height = self.getInputVideoSize()
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

		self.log.debug('Initializing Mixer-State')
		# FIXME

		bgMixerpad = self.mixingPipeline.get_by_name('mix').get_static_pad('sink_0')
		bgMixerpad.set_property('zorder', 0)

		self.log.debug('Launching Mixing-Pipeline')
		self.mixingPipeline.set_state(Gst.State.PLAYING)

	def getInputVideoSize(self):
		caps = Gst.Caps.from_string(self.caps)
		struct = caps.get_structure(0)
		_, width = struct.get_int('width')
		_, height = struct.get_int('height')

		return width, height


	def setScene(self, scene):
		# FIXME
		pass

	def getScene(self, scene):
		# FIXME
		pass


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
