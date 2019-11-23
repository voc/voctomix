#!/usr/bin/env python3
import logging
import re

from gi.repository import Gst, GLib

from lib.config import Config
from lib.sources.avsource import AVSource


class V4l2AVSource(AVSource):

    timer_resolution = 0.5

    def __init__(self, name):
        super().__init__('V4l2Source', name, False, True, show_no_signal=True)

        self.device = Config.getV4l2Device(name)
        self.name = name
        self.signalPad = None

        self.build_pipeline()

    def port(self):
        return "V4l2 device {}".format(self.device)

    def attach(self, pipeline):
        super().attach(pipeline)
        self.signalPad = pipeline.get_by_name(
            'v4l2videosrc-{}'.format(self.name))
        GLib.timeout_add(self.timer_resolution * 1000, self.do_timeout)

    def do_timeout(self):
        if self.inputSink:
            self.inputSink.set_property(
                'alpha', 1.0 if self.num_connections() > 0 else 0.0)
        # just come back
        return True

    def num_connections(self):
        return 1 if self.signalPad and self.signalPad.get_property('signal') else 0

    def __str__(self):
        return 'V4l2AVSource[{name}] reading device {device}'.format(
            name=self.name,
            device=self.device
        )

    def build_source(self):
        pipe = """
    v4l2src
        device={device}
""".format(device=self.device)

        # we may need to set things like width=1920,height=1080,format=YUY2,framerate=60/1 here
        pipe += """\
    ! video/x-raw
"""

        if self.build_deinterlacer():
            pipe += """\
    ! {deinterlacer}
""".format(deinterlacer=self.build_deinterlacer())

        pipe += """\
    ! videoconvert
    ! videoscale
    ! videorate
        name=vout-{name}
""".format(
            name=self.name
        )

        return pipe

    def build_videoport(self):
        return 'vout-{}.'.format(self.name)
