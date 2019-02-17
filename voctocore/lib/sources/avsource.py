#!/usr/bin/env python3
import logging
from abc import ABCMeta, abstractmethod

from lib.config import Config


class AVSource(object, metaclass=ABCMeta):

    def __init__(self, class_name, name,
                 has_audio=True, has_video=True,
                 num_streams=None):
        self.log = logging.getLogger("%s[%s]" % (class_name, name))

        assert has_audio or has_video

        self.class_name = class_name
        self.name = name
        self.has_audio = has_audio
        self.has_video = has_video
        self.num_streams = num_streams if num_streams else Config.getNumAudioStreams()
        self.bin = ""

    @abstractmethod
    def __str__(self):
        raise NotImplementedError(
            '__str__ not implemented for this source')

    def attach(self, pipeline):
        return

    def build_pipeline(self):
        self.bin = """
bin.(
    name={class_name}-{name}
""".format(class_name=self.class_name,name=self.name)

        self.bin += self.build_source()

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

    def build_source(self):
        return ""

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

    def num_connections(self):
        return 0

    def is_input(self):
        return True

    def section(self):
        return 'source.{}'.format(self.name)

    @abstractmethod
    def port(self):
        assert False, "port() not implemented in %s" % self.name

    @abstractmethod
    def build_audioport(self, audiostream):
        assert False, "build_audioport() not implemented in %s" % self.name

    @abstractmethod
    def build_videoport(self):
        assert False, "build_videoport() not implemented in %s" % self.name
