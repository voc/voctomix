#!/usr/bin/env python3
import logging
import gi

from gi.repository import Gst
from vocto.video_codecs import construct_video_encoder_pipeline
from vocto.audio_codecs import construct_audio_encoder_pipeline
from lib.args import Args
from lib.config import Config


class LocalPlayout():

    def __init__(self, source, port, use_audio_mix=False, audio_blinded=False):
        # create logging interface
        self.log = logging.getLogger('LocalPlayout'.format(source))

        # remember things
        self.source = source
        self._port = port

        # open bin
        self.bin = "" if Args.no_bins else """
            bin.(
                name=LocalPlayout
                """

        # video pipeline
        self.bin += """
                video-mix.
                ! {vcaps}
                ! queue
                    max-size-time=3000000000
                    name=queue-mux-video-localplayout
                {vpipeline}
                ! queue
                    max-size-time=3000000000
                    name=queue-mux-localplayout-{source}
                ! mux-localplayout-{source}.
                """.format(source=self.source,
                           vpipeline=construct_video_encoder_pipeline('localplayout'),
                           vcaps=Config.getVideoCaps())

        # audio pipeline
        if use_audio_mix or source in Config.getAudioSources(internal=True):
            self.bin += """
                {use_audio}audio-{audio_source}{audio_blinded}.
                ! queue
                    max-size-time=3000000000
                    name=queue-audio-localplayout-convert-{source}
                {apipeline}
                ! queue
                    max-size-time=3000000000
                    name=queue-mux-audio-{source}
                ! mux-localplayout-{source}.
                """.format(source=self.source,
                           apipeline=construct_audio_encoder_pipeline('localplayout'),
                           use_audio="" if use_audio_mix else "source-",
                           audio_source="mix" if use_audio_mix else self.source,
                           audio_blinded="-blinded" if Config.getBlinderEnabled() and audio_blinded else ""
                           )

        # mux pipeline
        self.bin += """
            mpegtsmux
                name=mux-localplayout-{source}
            ! queue
                max-size-time=3000000000
                name=queue-sink-localplayout-{source}
                leaky=downstream
            ! sink-localplayout-{source}.
            """.format(source=self.source)

        # sink pipeline
        self.bin += """
                srtserversink
                    name=sink-localplayout-{source}
                    uri=srt://:{port}
                """.format(source=self.source,
                           port=self._port)

        # close bin
        self.bin += "" if Args.no_bins else "\n)\n"

    def __str__(self):
        return 'LocalPlayout[{}] at port {}'.format(self.source, self._port)

    def port(self):
        return "srt://:{}".format(self._port)

    def num_connections(self):
        return 0

    def audio_channels(self):
        return Config.getNumAudioStreams()

    def video_channels(self):
        return 1

    def is_input(self):
        return False

    def attach(self, pipeline):
        self.pipeline = pipeline
