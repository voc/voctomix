#!/usr/bin/env python3
import logging
import re

from gi.repository import Gst, GLib

from lib.config import Config
from lib.sources.avsource import AVSource


class DeckLinkAVSource(AVSource):

    timer_resolution = 0.5

    def __init__(self, name, has_audio=True, has_video=True):
        super().__init__('DecklinkAVSource', name, has_audio, has_video)

        self.device = Config.getDeckLinkDeviceNumber(name)
        self.aconn = Config.getDeckLinkAudioConnection(name)
        self.vconn = Config.getDeckLinkVideoConnection(name)
        self.vmode = Config.getDeckLinkVideoMode(name)
        self.vfmt = Config.getDeckLinkVideoFormat(name)
        self.name = name

        self.signalPad = None
        self.build_pipeline()

    def port(self):
        return "Decklink #{}".format(self.device)

    def attach(self, pipeline):
        super().attach(pipeline)
        self.signalPad = pipeline.get_by_name(
            'decklinkvideosrc-{}'.format(self.name))
        GLib.timeout_add(self.timer_resolution * 1000, self.do_timeout)

    def do_timeout(self):
        self.inputSink.set_property(
            'alpha', 1.0 if self.num_connections() > 0 else 0.0)
        # just come back
        return True

    def num_connections(self):
        return 1 if self.signalPad and self.signalPad.get_property('signal') else 0


    def __str__(self):
        return 'DecklinkAVSource[{name}] reading card #{device}'.format(
            name=self.name,
            device=self.device
        )

    def build_source(self):
        # A video source is required even when we only need audio
        pipe = """
    decklinkvideosrc
        name=decklinkvideosrc-{name}
        device-number={device}
        connection={conn}
        video-format={fmt}
        mode={mode}
        drop-no-signal-frames=true
""".format(name=self.name,
            device=self.device,
            conn=self.vconn,
            mode=self.vmode,
            fmt=self.vfmt
        )

        if self.has_video:
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
                deinterlacer=self.build_deinterlacer(),
                name=self.name
            )
        else:
            pipe += """\
    ! fakesink
"""

        if self.has_audio:
            pipe += """
    decklinkaudiosrc
        name=decklinkaudiosrc-{name}
        device-number={device}
        connection={conn}
        channels={channels}
""".format( name=self.name,
            device=self.device,
            conn=self.aconn,
            channels=Config.getNumAudioStreams())

        return pipe

    def build_audioport(self):
        return 'decklinkaudiosrc-{name}.'.format(name=self.name)

    def build_videoport(self):
        return 'vout-{}.'.format(self.name)
