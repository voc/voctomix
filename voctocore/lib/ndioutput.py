#!/usr/bin/env python3
import logging
import socket

from gi.repository import Gst

from voctocore.lib.args import Args
from voctocore.lib.avnode import AVIONode
from voctocore.lib.config import Config


class NDIOutput(AVIONode):
    log: logging.Logger
    source: str
    bin: str
    ndi_name: str

    def __init__(self, source: str, use_audio_mix: bool=False, audio_blinded: bool=False, ndi_name: str='',
                 video_format: str='') -> None:
        # create logging interface
        self.log = logging.getLogger('NDIOutput[{}]'.format(source))

        # remember things
        self.source = source
        self.ndi_name = Config.getNDIPrefix() + ( ndi_name if ndi_name else source )

        self._video_conversion = ""
        if video_format and video_format != Config.getVideoCaps():
            self._video_conversion = """
                ! queue
                    max-size-time=3000000000
                    name=queue-video-ndi-convert-{source}
                ! videoconvert
                ! {video_format}
            """.format(
                source=self.source,
                video_format=video_format,
            )

        # open bin
        self.bin = "" if Args.no_bins else """
            bin.(
                name=NDIOutput-{source}
                """.format(source=self.source)

        # video pipeline
        if source not in Config.getVideoSources(internal=True):
            raise Exception(f'No video source with name "{source}". NDI does not work without a video stream.')
        self.bin += """
                video-{source}.
                ! {vcaps}
                {video_conversion}
                ! queue
                    max-size-time=3000000000
                    name=queue-ndi-mux-video-{source}
                ! ndi-mux-{source}.
                """.format(
                source=self.source,
                vcaps=Config.getVideoCaps(),
                video_conversion=self._video_conversion,
        )

        # audio pipeline
        if use_audio_mix or source in Config.getAudioSources(internal=True):
            self.bin += """
                {use_audio}audio-{audio_source}{audio_blinded}.
                ! queue
                    max-size-time=3000000000
                    name=queue-audio-ndi-convert-{source}
                ! audioconvert
                ! queue
                    max-size-time=3000000000
                    name=queue-ndi-mux-audio-{source}
                ! ndi-mux-{source}.audio
                """.format(
                source=self.source,
                use_audio="" if use_audio_mix else "source-",
                audio_source="mix" if use_audio_mix else self.source,
                audio_blinded="-blinded" if audio_blinded else ""
            )

        # playout pipeline
        self.bin += """
                ndisinkcombiner
                    name=ndi-mux-{source}
                ! ndisink
                    ndi-name="{ndi_name}"
                """.format(
            source=self.source,
            ndi_name=self.ndi_name,
        )

        # close bin
        self.bin += "" if Args.no_bins else "\n)\n"

    def port(self) -> str:
        return "0"

    def num_connections(self) -> int:
        return 0

    def audio_channels(self) -> int:
        return Config.getNumAudioStreams()

    def video_channels(self) -> int:
        return 1

    def is_input(self) -> bool:
        return False

    def __str__(self) -> str:
        return 'NDIOutput[{}]'.format(self.source)

    def attach(self, pipeline: Gst.Pipeline):
        self.pipeline = pipeline
