#!/usr/bin/env python3
import logging
import re

from gi.repository import Gst, GLib

from lib.config import Config
from lib.sources.avsource import AVSource


class RPICamAVSource(AVSource):

    timer_resolution = 0.5

    def __init__(self, name):
        super().__init__('RPICamSource', name, False, True, show_no_signal=False)

        self.device = Config.getRPICamDevice(name)
        self.width = Config.getRPICamWidth(name)
        self.height = Config.getRPICamHeight(name)
        self.framerate = Config.getRPICamFramerate(name)
        self.format = Config.getRPICamFormat(name)
        self.name = name
        self.signalPad = None

        self.build_pipeline()

    def port(self):
        return "RPICam device {}".format(self.device)

    def attach(self, pipeline):
        super().attach(pipeline)
        self.signalPad = pipeline.get_by_name(
            'rpicamvideosrc-{}'.format(self.name))
        GLib.timeout_add(self.timer_resolution * 1000, self.do_timeout)

    def num_connections(self):
        return 1 if self.signalPad and self.signalPad.get_property('signal') else 0

    def __str__(self):
        return 'RPICamAVSource[{name}] reading device {device}'.format(
            name=self.name,
            device=self.device
        )

    def get_valid_channel_numbers(self):
        return 0

    def build_source(self):
        pipe = """
            rpicamsrc
                bitrate=8000000 
                preview=false
                num-buffers=-1
            """

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
                ! videorate
                ! videoscale
                name=vout-{name}
        """.format(name=self.name)

        return pipe

    def build_videoport(self):
        return 'vout-{}.'.format(self.name)

    def get_nosignal_text(self):
        return super().get_nosignal_text() + "/rpicam%s" % self.device
