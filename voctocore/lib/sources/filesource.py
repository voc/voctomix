#!/usr/bin/env python3
import logging
import re

import os

from gi.repository import Gst

from voctocore.lib.config import Config
from voctocore.lib.sources.avsource import AVSource

class FileSource(AVSource):
    timer_resolution = 0.5

    def __init__(self, name, has_audio=True, has_video=True,
                 force_num_streams=None):
        self.location = Config.getLocation(name)
        self.audio_file = False
        (_, ext) = os.path.splitext(self.location)
        if ext in ['.mp2','.mp3']:
            assert not has_video
            self.audio_file=True

        super().__init__('FileSource', name, has_audio, has_video, show_no_signal=False)
        self.loop = Config.getLoop(name)
        self.build_pipeline()

    def __str__(self):
        return 'FileSource[{name}] displaying {location}'.format(
            name=self.name,
            location=self.location
        )

    def port(self):
        return os.path.basename(self.location)

    def num_connections(self):
        return 1

    def video_channels(self):
        return 1

    def build_source(self):
        source = """
              multifilesrc
                location={location}
                loop={loop}""".format(
            loop=self.loop,
            location=self.location
        )
        if not self.audio_file:
            source += """
            ! tsdemux
            """
        source +=  """
                name=file-{name}
            """.format(name=self.name)

        return source

    def build_videoport(self):
        return """
              file-{name}.
            ! mpegvideoparse
            ! mpeg2dec
            ! videoconvert
            ! videorate
            ! videoscale
            """.format(name=self.name)

    def build_audioport(self):
        return """
              file-{name}.
            ! mpegaudioparse
            ! mpg123audiodec
            ! audioconvert
            ! audioresample
            """.format(name=self.name)
