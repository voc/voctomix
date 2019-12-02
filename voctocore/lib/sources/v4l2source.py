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
        self.width = Config.getV4l2Width(name)
        self.height = Config.getV4l2Height(name)
        self.framerate = Config.getV4l2Framerate(name)
        self.format=Config.getV4l2Format(name)
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

    def get_valid_channel_numbers(self):
        return (0)

    def build_source(self):
        pipe = """
    v4l2src
        device={device}
""".format(device=self.device)

        pipe += """\
    ! video/x-raw,width={width},height={height},format={format},framerate={framerate}
""".format(width=self.width,
           height=self.height,
           format=self.format,
           framerate=self.framerate)

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
