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
        self.build_pipeline()

    def port(self):
        if self.has_video:
            if self.internal_audio_channels():
                return "({}+audio)".format(self.pattern)
            else:
                return "({})".format(self.pattern)
        else:
            if self.internal_audio_channels():
                return "(audio)"
        return "Test"

    def num_connections(self):
        return 1

    def __str__(self):
        return 'TestSource[{name}] (pattern #{pattern})'.format(
            name=self.name,
            pattern=self.pattern
        )

    def build_audioport(self):
        return """audiotestsrc
                      name=audiotestsrc-{name}
                      is-live=true""".format(name=self.name)

    def build_videoport(self):
        return """videotestsrc
                      name=videotestsrc-{name}
                      pattern={pattern}
                      is-live=true""".format(
            name=self.name,
            pattern=self.pattern
        )
