#!/usr/bin/env python3
import logging
import re

from voctocore.lib.config import Config
from voctocore.lib.sources.avsource import AVSource


class DeckLinkAVSource(AVSource):

    timer_resolution = 0.5

    def __init__(self, name, has_audio=True, has_video=True):
        super().__init__('DecklinkAVSource', name, has_audio, has_video, show_no_signal=True)

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

    def num_connections(self):
        return 1 if self.signalPad and self.signalPad.get_property('signal') else 0

    def get_valid_channel_numbers(self):
        return (2, 8, 16)

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
            """.format(name=self.name,
                       device=self.device,
                       conn=self.vconn,
                       mode=self.vmode,
                       fmt=self.vfmt
                       )

        # add rest of the video pipeline
        if self.has_video:
            # maybe add deinterlacer
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
        else:
            pipe += """\
                    ! fakesink
                    """

        if self.internal_audio_channels():
            pipe += """
                decklinkaudiosrc
                    name=decklinkaudiosrc-{name}
                    device-number={device}
                    connection={conn}
                    channels={channels}
                """.format(name=self.name,
                           device=self.device,
                           conn=self.aconn,
                           channels=self.internal_audio_channels())

        return pipe

    def build_audioport(self):
        return 'decklinkaudiosrc-{name}.'.format(name=self.name)

    def build_videoport(self):
        return 'vout-{}.'.format(self.name)

    def get_nosignal_text(self):
        return super().get_nosignal_text() + "/BM%d" % self.device
