#!/usr/bin/env python3
import logging
import re

from gi.repository import Gst

from voctocore.lib.avnode import AVNode
from voctocore.lib.config import Config
from voctocore.lib.clock import Clock
from voctocore.lib.args import Args

from typing import Optional


class Blinder(AVNode):
    log: logging.Logger
    acaps: str
    vcaps: str
    volume: float
    bin: str
    blindersources: list[str]
    livesources: list[str]
    blind_source: Optional[int]

    def __init__(self):
        self.log = logging.getLogger('Blinder')

        # remember some things
        self.acaps = Config.getAudioCaps()
        self.vcaps = Config.getVideoCaps()
        self.volume = Config.getBlinderVolume()
        self.blindersources = Config.getBlinderSources()

        # make sure blinder audio caps match program caps
        mixmatrix = Config.getAudioMixMatrix()
        self.mix_channels = len(mixmatrix[0])
        self.program_channels = len(mixmatrix)
        self.program_acaps = re.sub(r'channels=(\(int\))?\d+',
                                    f'channels={self.program_channels}',
                                    self.acaps)
        if self.program_channels == self.mix_channels:
            self.blinder_downmix = ""
        else:
            matrix = str(mixmatrix).replace("[", "<").replace("]", ">")
            self.blinder_downmix = f"""
            ! audiomixmatrix
                name=audiomixmatrix-blinder
                in_channels={self.mix_channels}
                out_channels={self.program_channels}
                matrix="{matrix}"
            """

        self.log.info('Configuring video blinders for %u sources',
                      len(self.blindersources))

        # open bin
        self.bin = "" if Args.no_bins else """
            bin.(
                name=blinders
                """

        # list blinders
        self.livesources = Config.getLiveSources()

        # add blinder pipelines
        for livesource in self.livesources:
            self.bin += """
                compositor
                    name=compositor-blinder-{livesource}
                ! queue
                    max-size-time=3000000000
                    name=queue-video-{livesource}-blinded
                ! tee
                    name=video-{livesource}-blinded

                video-{livesource}.
                ! queue
                    max-size-time=3000000000
                    name=queue-video-{livesource}-compositor-blinder-{livesource}
                ! compositor-blinder-{livesource}.
                """.format(livesource=livesource)

            for blindersource in self.blindersources:
                self.bin += """
                    video-{blindersource}.
                    ! queue
                        max-size-time=3000000000
                        name=queue-video-blinder-{blindersource}-compositor-blinder-{livesource}
                    ! compositor-blinder-{livesource}.
                    """.format(
                    blindersource=blindersource,
                    livesource=livesource
                )

        # Audiomixer
        self.bin += """
            audiomixer
                name=audiomixer-blinder
            ! audioamplify
                amplification={volume}
            ! capssetter
                caps={program_acaps}
            ! queue
                name=queue-audio-mix-blinded
                max-size-time=3000000000
            ! tee
                name=audio-mix-blinded

            audio-mix.
            ! queue
                max-size-time=3000000000
                name=queue-capssetter-blinder
            ! capssetter
                caps={program_acaps}
            ! queue
                max-size-time=3000000000
                name=queue-audiomixer-blinder
            ! audiomixer-blinder.
            """.format(program_acaps=self.program_acaps,
                       volume=Config.getBlinderVolume()
                       )

        # Source from the Blank-Audio-Tee into the Audiomixer
        self.bin += f"""
            audio-blinder.
            ! queue
                max-size-time=3000000000
                name=queue-audio-blinded-audiomixer-blinder{self.blinder_downmix}
            ! audiomixer-blinder.
            """

        # close bin
        self.bin += "" if Args.no_bins else "\n)\n"

        self.blind_source = 0 if len(self.blindersources) > 0 else None

    def __str__(self):
        return 'Blinder'

    def attach(self, pipeline):
        self.pipeline = pipeline
        self.applyMixerState()

    def applyMixerState(self):
        for livesource in self.livesources:
            self.applyMixerStateVideo(
                'compositor-blinder-{}'.format(livesource))
            self.applyMixerStateVideo(
                'compositor-blinder-{}'.format(livesource))
        self.applyMixerStateAudio('audiomixer-blinder')

    def applyMixerStateVideo(self, mixername):
        mixer = self.pipeline.get_by_name(mixername)
        if not mixer:
            self.log.error("Video mixer '%s' not found", mixername)
        else:
            mixer.get_static_pad('sink_0').set_property(
                'alpha', int(self.blind_source is None))
            for idx, name in enumerate(self.blindersources):
                blinder_pad = mixer.get_static_pad('sink_%u' % (idx + 1))
                blinder_pad.set_property(
                    'alpha', int(self.blind_source == idx))

    def applyMixerStateAudio(self, mixername):
        mixer = self.pipeline.get_by_name(mixername)
        if not mixer:
            self.log.error("Audio mixer '%s' not found", mixername)
        else:
            mixer.get_static_pad('sink_0').set_property(
                'volume', 1.0 if self.blind_source is None else 0.0)
            mixer.get_static_pad('sink_1').set_property(
                'volume', 0.0 if self.blind_source is None else 1.0)

    def setBlindSource(self, source):
        self.blind_source = source
        self.applyMixerState()
