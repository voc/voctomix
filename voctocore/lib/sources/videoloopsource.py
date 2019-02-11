#!/usr/bin/env python3
import logging
import re

from gi.repository import Gst

from lib.config import Config
from lib.sources.avsource import AVSource


class VideoLoopSource(AVSource):
    def __init__(self, name, has_audio=False, has_video=True):
        self.log = logging.getLogger('VideoLoopSource[{}]'.format(name))
        super().__init__(name, False, has_video)

        if has_audio:
            self.log.warning("Audio requested from video-only source")

        section = 'source.{}'.format(name)
        self.location = Config.get(section, 'location')

        self.launch_pipeline()

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

    def launch_pipeline(self):
        pipeline = """
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
        self.build_pipeline(pipeline)

    def build_audioport(self, audiostream):
        raise NotImplementedError(
            'build_audioport not implemented for this source')

    def build_videoport(self):
        return 'videoloop.'

    def restart(self):
        self.pipeline.set_state(Gst.State.NULL)
        self.launch_pipeline()
