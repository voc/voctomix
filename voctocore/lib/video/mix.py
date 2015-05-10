#!/usr/bin/python3
import logging
from gi.repository import Gst

from lib.config import Config

class VideoMix(object):
	log = logging.getLogger('VideoMix')

	mixingPipeline = None

	def __init__(self):
		caps = Config.get('mix', 'videocaps')

		names = Config.getlist('sources', 'video')
		self.log.info('Configuring Mixer for %u Sources', len(names))

		pipeline = """
			videomixer name=mix !
			{caps} !
			textoverlay text=mixer halignment=left valignment=top ypad=175 !
			intervideosink channel=video_mix
		""".format(
			caps=caps
		)

		for idx, name in enumerate(names):
			pipeline += """
				intervideosrc channel=video_{name}_mixer !
				{caps} !
				videoscale !
				capsfilter name=caps_{idx} !
				mix.
			""".format(
				name=name,
				caps=caps,
				idx=idx
			)

		self.log.debug('Launching Mixing-Pipeline:\n%s', pipeline)
		self.mixingPipeline = Gst.parse_launch(pipeline)
		self.mixingPipeline.set_state(Gst.State.PLAYING)

		mixerpad = self.mixingPipeline.get_by_name('mix').get_static_pad('sink_0')
		mixerpad.set_property('alpha', 0.5)
		mixerpad.set_property('xpos', 64)
		mixerpad.set_property('ypos', 64)

		mixerpad = self.mixingPipeline.get_by_name('mix').get_static_pad('sink_1')
		mixerpad.set_property('alpha', 0.2)

		capsilter = self.mixingPipeline.get_by_name('caps_1')
		capsilter.set_property('caps', Gst.Caps.from_string(
			'video/x-raw,width=320,height=180'))
