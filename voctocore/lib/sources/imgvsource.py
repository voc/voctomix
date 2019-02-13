#!/usr/bin/env python3
import logging
import re

from gi.repository import Gst

from lib.config import Config
from lib.sources.avsource import AVSource


class ImgVSource(AVSource):
    def __init__(self, name, has_audio=False, has_video=True):
        self.log = logging.getLogger('ImgVSource[{}]'.format(name))
        super().__init__(name, False, has_video)

        if has_audio:
            self.log.warning("Audio requested from video-only source")
        self.imguri = Config.getImageURI(name)
        self.launch_pipeline()

    def __str__(self):
        return 'ImgVSource[{name}] displaying {uri}'.format(
            name=self.name,
            uri=self.imguri
        )

    def port(self):
        m = re.search('.*/([^/]*)', self.imguri)
        return self.imguri

    def num_connections(self):
        return 1

    def video_channels(self):
        return 1

    def launch_pipeline(self):
        pipeline = """
    uridecodebin
        name=imgvsrc-{name}
        uri={uri}
    ! videoconvert
    ! videoscale
    ! imagefreeze
        name=img
""".format(
            name=self.name,
            uri=self.imguri
        )
        self.build_pipeline(pipeline)

    def build_audioport(self, audiostream):
        raise NotImplementedError(
            'build_audioport not implemented for this source')

    def build_videoport(self):
        return 'img.'

    def restart(self):
        self.pipeline.set_state(Gst.State.NULL)
        self.launch_pipeline()
