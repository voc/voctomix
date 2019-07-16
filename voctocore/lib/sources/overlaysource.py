#!/usr/bin/env python3
import logging
import re

from gi.repository import Gst

from lib.config import Config
from lib.sources.avsource import AVSource


class OverlaySource(AVSource):
    def __init__(self, name):
        super().__init__('OverlaySource', name, False, True)
        self.location = Config.getLocation(name)
        self.build_pipeline()

    def __str__(self):
        return 'OverlaySource[{name}] displaying {location}'.format(
            name=self.name,
            location=self.location
        )

    def port(self):
        return self.location

    def num_connections(self):
        return 1

    def video_channels(self):
        return 1

    def build_source(self):
        return """
    filesrc
        name=overlaysource-{name}
        location={location}
    ! pngdec
    ! imagefreeze 
        name=overlay
""".format(
            name=self.name,
            location=self.location
        )

    def build_audioport(self, audiostream):
        raise NotImplementedError(
            'build_audioport not implemented for this source')

    def build_videoport(self):
        return 'overlay.'

    def restart(self):
        self.pipeline.set_state(Gst.State.NULL)
        self.launch_pipeline()
