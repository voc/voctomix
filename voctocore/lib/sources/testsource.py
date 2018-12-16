#!/usr/bin/env python3
import logging

from gi.repository import Gst

from lib.config import Config
from lib.sources.avsource import AVSource

ALL_AUDIO_CAPS = Gst.Caps.from_string('audio/x-raw')
ALL_VIDEO_CAPS = Gst.Caps.from_string('video/x-raw')


class TestSource(AVSource):
    def __init__(self, name, outputs=None,
                 has_audio=True, has_video=True,
                 force_num_streams=None):
        self.log = logging.getLogger('TestSource[{}]'.format(name))
        AVSource.__init__(self, name, outputs,
                          has_audio, has_video,
                          force_num_streams)

        pipeline = """ """

        self.build_pipeline(pipeline)

        self.audio_caps = Gst.Caps.from_string(Config.get('mix', 'audiocaps'))
        self.video_caps = Gst.Caps.from_string(Config.get('mix', 'videocaps'))

        self.pipeline.set_state(Gst.State.PLAYING)

    def __str__(self):
        return 'TestSource[{name}]'.format(
            name=self.name
        )

    def build_audioport(self, audiostream):
        return 'audiotestsrc is-live=true'

    def build_videoport(self):
        return 'videotestsrc is-live=true'

    def restart(self):
        self.pipeline.set_state(Gst.State.NULL)
        self.launch_pipeline()
