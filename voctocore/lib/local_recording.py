#!/usr/bin/env python3
import datetime
import logging

import gi
from gi.repository import Gst
from voctocore.lib.args import Args
from voctocore.lib.config import Config

from vocto.audio_codecs import construct_audio_encoder_pipeline
from vocto.video_codecs import construct_video_encoder_pipeline


class LocalRecordingSink:
    log: logging.Logger
    source: str
    _port: int
    bin: str
    """
    The local playout class handels outputs for the voctocore that are played out directly by the gstreamer pipline.
    """

    def __init__(self, source: str, port: int, use_audio_mix: bool=False, audio_blinded: bool=False) -> None:
        # create logging interface
        self.log = logging.getLogger("LocalRecordingSink".format(source))

        # remember things
        self.source = source
        self._port = port

        # open bin
        self.bin = (
            ""
            if Args.no_bins
            else """
            bin.(
                name=LocalRecordingSink
                """
        )

        # video pipeline
        self.bin += """
                video-mix.
                ! {vcaps}
                ! queue
                    max-size-time=3000000000
                    name=queue-mux-video-localplayout
                {vpipeline} ! h264parse config-interval=1
                ! queue
                    max-size-time=3000000000
                    name=queue-mux-localplayout-{source}
                ! tee name=videomix-localplayout-{source}
                """.format(
            source=self.source,
            vpipeline=construct_video_encoder_pipeline(Config, "localplayout"),
            vcaps=Config.getVideoCaps(),
        )

        self.bin += """
            videomix-localplayout-{source}. ! queue ! mux-localplayout-{source}.
            videomix-localplayout-{source}. ! queue leaky=downstream ! recording-{source}.
            """.format(
            source=self.source
        )

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
                ! tee name=audiomix-localplayout-{source}
                """.format(
                source=self.source,
                apipeline=construct_audio_encoder_pipeline(Config,"localplayout"),
                use_audio="" if use_audio_mix else "source-",
                audio_source="mix" if use_audio_mix else self.source,
                audio_blinded=(
                    "-blinded" if Config.getBlinderEnabled() and audio_blinded else ""
                ),
            )

            self.bin += """
                audiomix-localplayout-{source}. ! queue ! mux-localplayout-{source}.
                audiomix-localplayout-{source}. ! queue ! recording-{source}.audio_0
                """.format(
                source=self.source
            )

        # recording pipeline
        self.bin += """
            splitmuxsink async-finalize=true max-size-time=300000000000 muxer-factory=mpegtsmux location="/mnt/video/default.ts" name=recording-{source}
            """.format(
            source=self.source
        )

        # mux pipeline
        self.bin += """
            mpegtsmux
                name=mux-localplayout-{source}
            ! queue
                max-size-time=3000000000
                name=queue-sink-localplayout-{source}
                leaky=downstream
            ! tee name=source-localplayout-{source}
            """.format(
            source=self.source
        )

        # close bin
        self.bin += "" if Args.no_bins else "\n)\n"

    def __str__(self) -> str:
        return "LocalRecordingSink[{}] at port {}".format(self.source, self._port)

    def port(self) -> str:
        return "srt://:{}".format(self._port)

    def num_connections(self) -> int:
        return 0

    def audio_channels(self) -> int:
        return Config.getNumAudioStreams()

    def video_channels(self) -> int:
        return 1

    def is_input(self) -> bool:
        return False

    def format_location_callback(self, splitmux, fragment_id: str) -> str:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        return "/mnt/video/isdn-{timestamp}-{fragment_id}.ts".format(
            timestamp=timestamp, fragment_id=fragment_id
        )

    def attach(self, pipeline: Gst.Pipeline):
        if Config.getRecordingEnabled():
            recording_sink = pipeline.get_by_name(
                "recording-{source}".format(source=self.source)
            )
            if recording_sink is None:
                raise Exception("could not find pipeline element for {}".format(self))
            recording_sink.connect("format-location", self.format_location_callback)
