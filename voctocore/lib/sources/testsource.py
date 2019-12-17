#!/usr/bin/env python3
import logging

from configparser import NoOptionError
from gi.repository import Gst

from lib.config import Config
from lib.sources.avsource import AVSource


class TestSource(AVSource):
    def __init__(self, name, has_audio=True, has_video=True,
                 force_num_streams=None):
        super().__init__('TestSource', name, has_audio, has_video,
                         force_num_streams)

        self.name = name
        self.pattern = Config.getTestPattern(name)
        self.wave = Config.getTestWave(name)
        self.build_pipeline()

    def port(self):
        if self.has_video:
            if self.internal_audio_channels():
                return "(AV:{}+{})".format(self.pattern, self.wave)
            else:
                return "(V:{})".format(self.pattern)
        else:
            if self.internal_audio_channels():
                return "(A:{})".format(self.wave)
        return "Test"

    def num_connections(self):
        return 1

    def __str__(self):
        return 'TestSource[{name}] ({pattern}, {wave})'.format(
            name=self.name,
            pattern=self.pattern,
            wave=self.wave
        )

    def build_audioport(self):
        # a volume of 0.126 is ~18dBFS
        return """audiotestsrc
                      name=audiotestsrc-{name}
                      do-timestamp=true
                      freq=1000
                      volume=0.126
                      wave={wave}
                      is-live=true""".format(
            name=self.name,
            wave=self.wave,
        )

    def build_videoport(self):
        return """videotestsrc
                      name=videotestsrc-{name}
                      do-timestamp=true
                      pattern={pattern}
                      is-live=true""".format(
            name=self.name,
            pattern=self.pattern
        )
