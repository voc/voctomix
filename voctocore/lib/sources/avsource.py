import logging
from abc import ABCMeta, abstractmethod
from gi.repository import Gst

from lib.config import Config
from lib.clock import Clock


class AVSource(object, metaclass=ABCMeta):
    def __init__(self, name, outputs=None, has_audio=True, has_video=True):
        if not self.log:
            self.log = logging.getLogger('AVSource[{}]'.format(name))

        if outputs is None:
            outputs = [name]

        assert has_audio or has_video

        self.name = name
        self.has_audio = has_audio
        self.has_video = has_video
        self.outputs = outputs
        self.pipeline = None

    def __str__(self):
        return 'AVSource[{name}]'.format(
            name=self.name
        )

    def build_pipeline(self, pipeline, aelem=None, velem=None):
        if self.has_audio and aelem:
            pipeline += """
                {aelem}. !
                {acaps} !
                queue !
                tee name=atee
            """.format(
                aelem=aelem,
                acaps=Config.get('mix', 'audiocaps')
            )

            for output in self.outputs:
                pipeline += """
                    atee. ! queue ! interaudiosink channel=audio_{output}
                """.format(
                    output=output
                )

        if self.has_video and velem:
            pipeline += """
                {velem}. !
                {vcaps} !
                queue !
                tee name=vtee
            """.format(
                velem=velem,
                deinterlacer=self.build_deinterlacer(),
                vcaps=Config.get('mix', 'videocaps')
            )

            for output in self.outputs:
                pipeline += """
                    vtee. ! queue ! intervideosink channel=video_{output}
                """.format(
                    output=output
                )

        self.log.debug('Launching Source-Pipeline:\n%s', pipeline)
        self.pipeline = Gst.parse_launch(pipeline)
        self.pipeline.use_clock(Clock)

        self.log.debug('Binding End-of-Stream-Signal on Source-Pipeline')
        self.pipeline.bus.add_signal_watch()
        self.pipeline.bus.connect("message::eos", self.on_eos)
        self.pipeline.bus.connect("message::error", self.on_error)

    def build_deinterlacer(self):
        deinterlace_config = self.get_deinterlace_config()

        if deinterlace_config == "yes":
            return "yadif mode=interlaced"

        elif deinterlace_config == "no":
            return ""

        else:
            raise RuntimeError(
                "Unknown Deinterlace-Mode on source {} configured: {}"
                .format(self.name, deinterlace_config))

    def get_deinterlace_config(self):
        section = 'source.{}'.format(self.name)
        deinterlace_config = Config.get(section, 'deinterlace', fallback="no")
        return deinterlace_config

    def on_eos(self, bus, message):
        self.log.debug('Received End-of-Stream-Signal on Source-Pipeline')

    def on_error(self, bus, message):
        self.log.warning('Received Error-Signal on Source-Pipeline')
        (error, debug) = message.parse_error()
        self.log.debug('Error-Details: #%u: %s', error.code, debug)

    @abstractmethod
    def restart(self):
        raise NotImplementedError('Restarting not implemented for this source')
