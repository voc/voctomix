#!/usr/bin/env python3
import logging
import re

from gi.repository import Gst

from lib.config import Config
from lib.sources.avsource import AVSource


class LoopSource(AVSource):
    timer_resolution = 0.5

    def __init__(self, name, has_audio=True, has_video=True,
                 force_num_streams=None):
        super().__init__('LoopSource', name, has_audio, has_video, show_no_signal=True)
        self.location = Config.getLocation(name)
        self.build_pipeline()

    def __str__(self):
        return 'LoopSource[{name}] displaying {location}'.format(
            name=self.name,
            location=self.location
        )

    def port(self):
        m = re.search('.*/([^/]*)', self.location)
        return self.location

    def num_connections(self):
        return 1

    def video_channels(self):
        return 1

    def build_source(self):
        return """
             multifilesrc
               location={location}
               loop=true
            ! decodebin
               name=videoloop-{name}
            """.format(
            name=self.name,
            location=self.location
        )

    def build_videoport(self):
        return """
              videoloop-{name}.
            ! videoconvert
            ! videorate
            ! videoscale
            """.format(name=self.name)

    def build_audioport(self):
        return """
              videoloop-{name}.
            ! audioconvert
            ! audioresample
            """.format(name=self.name)