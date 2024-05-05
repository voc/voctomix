#!/usr/bin/env python3
import logging
from configparser import NoOptionError

from gi.repository import Gst
from lib.config import Config
from lib.sources.avsource import AVSource


class AlsaAudioSource(AVSource):

    def __init__(self, name, has_audio=True, has_video=False, force_num_streams=None):
        super().__init__(
            'AlsaAudioSource', name, has_audio, has_video, force_num_streams
        )
        self.device = Config.getAlsaAudioDevice(name)
        self.name = name

        self.build_pipeline()

    def port(self):
        return "AlsaAudio {}".format(self.device)

    def num_connections(self):
        return 1

    def __str__(self):
        return 'AlsaAudioSource[{name}] ({device})'.format(
            name=self.name, device=self.device
        )

    def build_audioport(self):
        return """alsasrc
                    name=alsaaudiosrc-{name}
                    device={device}
                  ! audioconvert
                  ! audioresample
                """.format(
            device=self.device,
            name=self.name,
        )
