#!/usr/bin/env python3
import logging
import re

from voctocore.lib.config import Config
from voctocore.lib.sources.avsource import AVSource


class AJAAVSource(AVSource):

    timer_resolution = 0.5

    def __init__(self, name, has_audio=True, has_video=True):
        super().__init__('AJAAVSource', name, has_audio, has_video, show_no_signal=True)

        self.device = Config.getAJADeviceIdentifier(name)
        self.input_channel = Config.getAJAInputChannel(name)
        self.vmode = Config.getAJAVideoMode(name)
        self.asrc = Config.getAJAAudioSource(name)
        self.name = name

        self.signalPad = None
        self.build_pipeline()

    def port(self):
        return "AJA #{}".format(self.device)

    def attach(self, pipeline):
        super().attach(pipeline)
        self.signalPad = pipeline.get_by_name(
            f'ajasrc-{self.name}')

    def num_connections(self):
        return 1 if self.signalPad and self.signalPad.get_property('signal') else 0

    def get_valid_channel_numbers(self):
        return (2, 8, 16)

    def __str__(self):
        return f'AJAAVSource[{self.name}] reading card #{self.device}'

    def build_source(self):
        pipe = f"""
            ajasrc
                name=ajasrc-{self.name}
                device-identifier={self.device}
                channel={self.input_channel}
                video-format={self.vmode}
            ! ajasrcdemux
                name=ajasrcdemux-{self.name}
            """

        # add rest of the video pipeline
        if self.has_video:
            pipe += f"""\
                ajasrcdemux-{self.name}.video
                """

            # maybe add deinterlacer
            if deinterlacer := self.build_deinterlacer():
                pipe += f"""\
                    ! {deinterlacer}
                    """

            pipe += f"""\
                ! videoconvert
                ! videoscale
                ! videorate
                    name=vout-{self.name}
                """

        if chans := self.internal_audio_channels():
            pipe += f"""\
                ajasrcdemux-{self.name}.audio
                ! audioconvert
            """

            if chans < 16:
                # Take the first {chans} channels.
                pipe += f"""\
                    ! audiomixmatrix
                        in-channels=16
                        out-channels={chans}
                        mode=first-channels
                """
            pipe += f"""\
                name=aout-{self.name}
            """

        return pipe

    def build_audioport(self):
        return f'aout-{self.name}.'

    def build_videoport(self):
        return f'vout-{self.name}.'

    def get_nosignal_text(self):
        return f"{super().get_nosignal_text()}/AJA{self.device}"
