#!/usr/bin/env python3
import logging
import re
import os

from gi.repository import Gst

from lib.config import Config
from lib.sources.avsource import AVSource


class ImgVSource(AVSource):
    def __init__(self, name):
        super().__init__('ImgVSource', name, False, True)
        self.imguri = Config.getImageURI(name)
        self.build_pipeline()

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

    def build_source(self):
        return """
    uridecodebin
        name=imgvsrc-{name}
        uri={uri}
    ! videoconvert
    ! videoscale
    ! imagefreeze
        name=img-{name}
""".format(
            name=self.name,
            uri=self.imguri
        )

    def build_audioport(self, audiostream):
        raise NotImplementedError(
            'build_audioport not implemented for this source')

    def build_videoport(self):
        return "img-{name}.".format(name=self.name)

    def restart(self):
        self.pipeline.set_state(Gst.State.NULL)
        self.launch_pipeline()
