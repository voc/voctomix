#!/usr/bin/env python3
import logging
import re

from gi.repository import Gst

from lib.config import Config
from lib.sources.avsource import AVSource


class VideoLoopSource(AVSource):
    def __init__(self, name):
        super().__init__('VideoLoopSource', name, False, True)
        self.location = Config.getLocation(name)
        self.build_pipeline()

    def __str__(self):
        return 'VideoLoopSource[{name}] displaying {location}'.format(
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
        name=videoloop-{name}
       location={location}
       loop=true
    ! decodebin
    ! videoconvert
    ! videoscale
        name=videoloop
""".format(
            name=self.name,
            location=self.location
        )

    def build_videoport(self):
        return 'videoloop.'
