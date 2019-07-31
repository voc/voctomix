#!/usr/bin/env python3
import logging
import re

from gi.repository import Gst, GLib

from lib.config import Config
from lib.sources.avsource import AVSource


class DeckLinkAVSource(AVSource):

    timer_resolution = 0.5

    def __init__(self, name, has_audio=True, has_video=True):
        super().__init__('DecklinkAVSource', name, has_audio, has_video)

        self.device = Config.getDeckLinkDeviceNumber(name)
        self.aconn = Config.getDeckLinkAudioConnection(name)
        self.vconn = Config.getDeckLinkVideoConnection(name)
        self.vmode = Config.getDeckLinkVideoMode(name)
        self.vfmt = Config.getDeckLinkVideoFormat(name)
        self.audiostreams = Config.getDeckLinkAudioStreamMap(name)
        self.name = name

        self.fallback_default = not self.audiostreams
        if self.fallback_default:
            self.log.info("no audiostream-mapping defined,"
                          "defaulting to mapping channel 0+1 to first stream")

        self._warn_incorrect_number_of_streams()

        self.required_input_channels = \
            self._calculate_required_input_channels()

        self.log.info("configuring decklink-input to %u channels",
                      self.required_input_channels)

        min_gst_multi_channels = (1, 12, 3)
        if self.required_input_channels > 2 and \
                Gst.version() < min_gst_multi_channels:

            self.log.warning(
                'GStreamer version %s is probably too to use more then 2 '
                'channels on your decklink source. officially supported '
                'since %s',
                tuple(Gst.version()), min_gst_multi_channels)

        self.signalPad = None
        self.build_pipeline()

    def port(self):
        return "Decklink #{}".format(self.device)

    def attach(self, pipeline):
        super().attach(pipeline)
        self.signalPad = pipeline.get_by_name('decklinkvideosrc-{}'.format(self.name))
        GLib.timeout_add(self.timer_resolution * 1000, self.do_timeout)

    def do_timeout(self):
        self.inputSink.set_property('alpha', 1.0 if self.num_connections() > 0 else 0.0)
        # just come back
        return True

    def num_connections(self):
        return 1 if self.signalPad and self.signalPad.get_property('signal') else 0

    def audio_channels(self):
        if len(self.audiostreams) == 0:
            return 1
        else:
            return len(self.audiostreams)

    def _calculate_required_input_channels(self):
        required_input_channels = 0
        for audiostream, mapping in self.audiostreams.items():
            left, right = mapping
            required_input_channels = max(required_input_channels, left + 1)
            if right:
                required_input_channels = max(required_input_channels,
                                              right + 1)

        required_input_channels = \
            self._round_decklink_channels(required_input_channels)

        return required_input_channels

    def _round_decklink_channels(self, required_input_channels):
        if required_input_channels > 16:
            raise RuntimeError(
                "Decklink-Devices support up to 16 Channels,"
                "you requested {}".format(required_input_channels))

        elif required_input_channels > 8:
            required_input_channels = 16

        elif required_input_channels > 2:
            required_input_channels = 8

        else:
            required_input_channels = 2

        return required_input_channels

    def _parse_audiostreamsping(self, mapping):
        m = re.match(r'(\d+)\+(\d+)', mapping)
        if m:
            return (int(m.group(1)), int(m.group(2)),)
        else:
            return (int(mapping), None,)

    def _warn_incorrect_number_of_streams(self):
        num_streams = Config.getNumAudioStreams()
        for audiostream, mapping in self.audiostreams.items():
            if audiostream >= num_streams:
                raise RuntimeError(
                    "Mapping-Configuration for Stream 0 to {} found,"
                    "but only {} enabled"
                    .format(audiostream, num_streams))

    def __str__(self):
        return 'DecklinkAVSource[{name}] reading card #{device}'.format(
            name=self.name,
            device=self.device
        )

    def build_source(self):
        # A video source is required even when we only need audio
        pipe = """
    decklinkvideosrc
        name=decklinkvideosrc-{name}
        device-number={device}
        connection={conn}
        video-format={fmt}
        mode={mode}
""".format( name=self.name,
            device=self.device,
            conn=self.vconn,
            mode=self.vmode,
            fmt=self.vfmt
        )

        if self.has_video:
            if self.build_deinterlacer():
                pipe += """\
    ! {deinterlacer}
""".format(deinterlacer=self.build_deinterlacer())

            pipe += """\
    ! videoconvert
    ! videoscale
    ! videorate
        name=vout-{name}
""".format(
                deinterlacer=self.build_deinterlacer(),
                name=self.name
            )
        else:
            pipe += """\
    ! fakesink
"""

        if self.has_audio:
            pipe += """
    decklinkaudiosrc
        name=decklinkaudiosrc-{name}
""".format( name=self.name )
            if self.required_input_channels > 2:
                pipe += """\
        channels={}
""".format(self.required_input_channels)

            pipe += """\
        device-number={device}
        connection={conn}
""".format(
                device=self.device,
                conn=self.aconn)

            if not self.fallback_default:
                pipe += """\
    ! deinterleave
"""
            pipe += """\
        name=aout-{name}
""".format(name=self.name)

            for audiostream, mapping in self.audiostreams.items():
                left, right = mapping
                if right is not None:
                    self.log.info(
                        "mapping decklink input-channels {left} and {right}"
                        "as left and right to output-stream {audiostream}"
                        .format(left=left,
                                right=right,
                                audiostream=audiostream))

                    pipe += """
    interleave
        name=i-{name}-{audiostream}

    aout-{name}.src_{left}
    ! queue
        name=queue-decklink-audio-{name}-{audiostream}-left
    ! i-{name}-{audiostream}.sink_0

    aout-{name}.src_{right}
    ! queue
        name=queue-decklink-audio-{name}-{audiostream}-right
    ! i-{name}-{audiostream}.sink_1
""".format(
                        left=left,
                        right=right,
                        name=self.name,
                        audiostream=audiostream
                    )
                else:
                    self.log.info(
                        "mapping decklink input-channel {channel} "
                        "as left and right to output-stream {audiostream}"
                        .format(channel=left,
                                audiostream=audiostream))

                    pipe += """
    interleave
        name=i-{name}-{audiostream}

    aout-{name}.src_{channel}
    ! tee
        name=t-{name}-{audiostream}

    t-{name}-{audiostream}.
    ! queue
        name=queue-decklink-audio-{name}-{audiostream}-left
    ! i-{name}-{audiostream}.sink_0

    t-{name}-{audiostream}.
    ! queue
        name=queue-decklink-audio-{name}-{audiostream}-right
    ! i-{name}-{audiostream}.sink_1
""".format(
                        channel=left,
                        name=self.name,
                        audiostream=audiostream
                    )

        return pipe

    def build_audioport(self, audiostream):
        if self.fallback_default and audiostream == 0:
            return "aout-{}.".format(self.name)

        if audiostream in self.audiostreams:
            return 'i-{name}-{audiostream}.'.format(name=self.name, audiostream=audiostream)

    def build_videoport(self):
        return 'vout-{}.'.format(self.name)
