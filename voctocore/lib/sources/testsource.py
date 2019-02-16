#!/usr/bin/env python3/
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

        self.pattern = Config.getTestPattern(name)
        self.build_pipeline()

    def port(self):
        return "(TEST)"

    def num_connections(self):
        return 1

    def __str__(self):
        return 'TestSource[{name}] (pattern #{pattern})'.format(
            name=self.name,
            pattern=self.pattern
        )

    def build_audioport(self, audiostream):
        return """audiotestsrc
        is-live=true"""

    def build_videoport(self):
        return """
    videotestsrc
        pattern={}
        is-live=true""".format(self.pattern)
