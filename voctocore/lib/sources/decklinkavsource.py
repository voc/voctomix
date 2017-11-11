import logging
import re

from gi.repository import Gst

from lib.config import Config
from lib.sources.avsource import AVSource


class DeckLinkAVSource(AVSource):
    def __init__(self, name, outputs=None, has_audio=True, has_video=True):
        self.log = logging.getLogger('DecklinkAVSource[{}]'.format(name))
        super().__init__(name, outputs, has_audio, has_video)

        section = 'source.{}'.format(name)

        # Device number, default: 0
        self.device = Config.get(section, 'devicenumber', fallback=0)

        # Audio connection, default: Automatic
        self.aconn = Config.get(section, 'audio_connection', fallback='auto')

        # Video connection, default: Automatic
        self.vconn = Config.get(section, 'video_connection', fallback='auto')

        # Video mode, default: 1080i50
        self.vmode = Config.get(section, 'video_mode', fallback='1080i50')

        self.audiostream_map = {}
        for key in Config[section]:
            value = Config.get(section, key)
            m = re.match('audiostream\[(\d+)\]', key)
            if m:
                audiostream = int(m.group(1))
                self.audiostream_map[audiostream] = value

        if len(self.audiostream_map) == 0:
            self.log.info("no audiostream-mapping defined, defaulting to mapping channel 0+1 to first stream")
            self.audiostream_map = {0: '0+1'}

        self.log.info("audiostream_map: %s", self.audiostream_map)

        self.required_input_channels = 0
        for audiostream, mapping in self.audiostream_map.items():
            left, right = self._parse_audiostream_mapping(mapping)
            self.required_input_channels = max(self.required_input_channels, left + 1)
            if right:
                self.required_input_channels = max(self.required_input_channels, right + 1)

        if self.required_input_channels > 8:
            self.required_input_channels = 16
        elif self.required_input_channels > 2:
            self.required_input_channels = 8
        else:
            self.required_input_channels = 2

        self.log.info("configuring decklink-input to %u channels", self.required_input_channels)

        self.launch_pipeline()

    def _parse_audiostream_mapping(self, mapping):
        m = re.match('(\d+)\+(\d+)', mapping)
        if m:
            return (int(m.group(1)), int(m.group(2)),)
        else:
            return (int(mapping), None,)

    def __str__(self):
        return 'DecklinkAVSource[{name}] reading card #{device}'.format(
            name=self.name,
            device=self.device
        )

    def launch_pipeline(self):
        # A video source is required even when we only need audio
        pipeline = """
            decklinkvideosrc
                {channels}
                device-number={device}
                connection={conn}
                mode={mode} !
        """.format(
            channels="channels={}".format(self.required_input_channels) if self.required_input_channels > 2 else "",
            device=self.device,
            conn=self.vconn,
            mode=self.vmode
        )

        if self.has_video:
            pipeline += """
                {deinterlacer}
                videoconvert !
                videoscale !
                videorate name=vout
            """.format(
                deinterlacer=self.build_deinterlacer()
            )
        else:
            pipeline += """
                fakesink
            """

        if self.has_audio:
            pipeline += """
                decklinkaudiosrc
                    device-number={device}
                    connection={conn} ! deinterleave name=aout
            """.format(
                device=self.device,
                conn=self.aconn
            )

            for audiostream, mapping in self.audiostream_map.items():
                left, right = self._parse_audiostream_mapping(mapping)
                if right != None:
                    self.log.info(
                        "mapping decklink input-channels {left} and {right} as left and right "
                        "to output-stream {audiostream}".format(
                            left=left,
                            right=right,
                            audiostream=audiostream))

                    pipeline += """
                        interleave name=i{audiostream}

                        aout.src_{left} ! queue ! i{audiostream}.sink_0
                        aout.src_{right} ! queue ! i{audiostream}.sink_1
                    """.format(
                        left=left,
                        right=right,
                        audiostream=audiostream
                    )
                else:
                    self.log.info(
                        "mapping decklink input-channel {channel} as left and right "
                        "to output-stream {audiostream}".format(
                            channel=left,
                            audiostream=audiostream))

                    pipeline += """
                        interleave name=i{audiostream}
                        aout.src_{channel} ! tee name=t{audiostream}

                        t{audiostream}. ! queue ! i{audiostream}.sink_0
                        t{audiostream}. ! queue ! i{audiostream}.sink_1
                    """.format(
                        channel=left,
                        audiostream=audiostream
                    )

        self.build_pipeline(pipeline)
        self.pipeline.set_state(Gst.State.PLAYING)

    def build_deinterlacer(self):
        deinterlacer = super().build_deinterlacer()
        if deinterlacer != '':
            deinterlacer += ' !'

        return deinterlacer

    def build_audioport(self, audiostream):
        if audiostream in self.audiostream_map:
            return 'i{}.'.format(audiostream)

    def build_videoport(self):
        return 'vout.'

    def restart(self):
        self.pipeline.set_state(Gst.State.NULL)
        self.launch_pipeline()
