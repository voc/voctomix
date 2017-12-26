import logging
from abc import ABCMeta, abstractmethod

from gi.repository import Gst

from lib.config import Config
from lib.clock import Clock


class AVSource(object, metaclass=ABCMeta):
    def __init__(self, name, outputs=None,
                 has_audio=True, has_video=True,
                 force_num_streams=None):
        if not self.log:
            self.log = logging.getLogger('AVSource[{}]'.format(name))

        if outputs is None:
            outputs = [name]

        assert has_audio or has_video

        self.name = name
        self.has_audio = has_audio
        self.has_video = has_video
        self.outputs = outputs
        self.force_num_streams = force_num_streams
        self.pipeline = None

    def __str__(self):
        return 'AVSource[{name}]'.format(
            name=self.name
        )

    def build_pipeline(self, pipeline):
        if self.has_audio:
            num_streams = self.force_num_streams
            if num_streams is None:
                num_streams = Config.getint('mix', 'audiostreams')

            for audiostream in range(0, num_streams):
                audioport = self.build_audioport(audiostream)
                if not audioport:
                    continue

                pipeline += """
                    {audioport} !
                    {acaps} !
                    queue !
                    tee name=atee_stream{audiostream}
                """.format(
                    audioport=audioport,
                    acaps=Config.get('mix', 'audiocaps'),
                    audiostream=audiostream,
                )

                for output in self.outputs:
                    pipeline += """
                        atee_stream{audiostream}. ! queue ! interaudiosink
                            channel=audio_{output}_stream{audiostream}
                    """.format(
                        output=output,
                        audiostream=audiostream,
                    )

        if self.has_video:
            pipeline += """
                {videoport} !
                {vcaps} !
                queue !
                tee name=vtee
            """.format(
                videoport=self.build_videoport(),
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
            return "videoconvert ! yadif mode=interlaced"

        elif deinterlace_config == "assume-progressive":
            return "capssetter " \
                   "caps=video/x-raw,interlace-mode=progressive"

        elif deinterlace_config == "no":
            return ""

        else:
            raise RuntimeError(
                "Unknown Deinterlace-Mode on source {} configured: {}".
                format(self.name, deinterlace_config))

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
    def build_audioport(self, audiostream):
        raise NotImplementedError(
            'build_audioport not implemented for this source')

    @abstractmethod
    def build_videoport(self):
        raise NotImplementedError(
            'build_videoport not implemented for this source')

    @abstractmethod
    def restart(self):
        raise NotImplementedError('Restarting not implemented for this source')
