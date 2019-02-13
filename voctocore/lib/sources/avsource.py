#!/usr/bin/env python3
import logging
from abc import ABCMeta, abstractmethod

from lib.config import Config


class AVSource(object, metaclass=ABCMeta):

    def __init__(self, name, has_audio=True, has_video=True,
                 num_streams=None):
        if not self.log:
            self.log = logging.getLogger('AVSource[{}]'.format(name))

        assert has_audio or has_video

        self.name = name
        self.has_audio = has_audio
        self.has_video = has_video
        self.num_streams = num_streams if num_streams else Config.getNumAudioStreams()
        self.bin = ""

    @abstractmethod
    def __str__(self):
        return 'AVSource[{name}]'.format(
            name=self.name
        )

    def attach(self, pipeline):
        return

    def build_pipeline(self, pipeline):
        self.bin = """
bin.(
    name=AVSource-{name}
""".format(name=self.name)

        self.bin += pipeline

        if self.has_audio:
            for audiostream in range(0, self.num_streams):
                audioport = self.build_audioport(audiostream)
                if not audioport:
                    continue

                self.bin += """
    {audioport}
    ! {acaps}
    ! tee
        name=audio-{name}-{audiostream}""".format(
                    audioport=audioport,
                    audiostream=audiostream,
                    acaps=Config.getAudioCaps(),
                    name=self.name
                )

        if self.has_video:
            self.bin += """
    {videoport}
    ! {vcaps}
    ! tee
        name=video-{name}""".format(
                videoport=self.build_videoport(),
                name=self.name,
                vcaps=Config.getVideoCaps()
            )

        self.bin += """
)
"""

    def build_deinterlacer(self):
        deinterlace_config = Config.getSourceDeinterlace(self.name)

        if deinterlace_config == "yes":
            return "videoconvert ! yadif mode=interlaced"
        elif deinterlace_config == "assume-progressive":
            return "capssetter " \
                   "caps=video/x-raw,interlace-mode=progressive"
        elif deinterlace_config == "no":
            return None
        else:
            raise RuntimeError(
                "Unknown Deinterlace-Mode on source {} configured: {}".
                format(self.name, deinterlace_config))

    def video_channels(self):
        return 1 if self.has_video else 0

    def audio_channels(self):
        return 1 if self.has_audio else 0

    @abstractmethod
    def port(self):
        raise NotImplementedError(
            'port() not implemented for this source')

    def num_connections(self):
        return 0

    def is_input(self):
        return True

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
