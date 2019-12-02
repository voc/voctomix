#!/usr/bin/env python3
import logging

from gi.repository import Gst

from lib.config import Config
from lib.clock import Clock
from lib.args import Args


class Blinder(object):
    log = logging.getLogger('Blinder')

    def __init__(self):
        self.acaps = Config.getAudioCaps()
        self.vcaps = Config.getVideoCaps()

        self.names = Config.getBlinderSources()
        self.log.info('Configuring Blinder video %u Sources',
                      len(self.names))

        self.volume = Config.getBlinderVolume()

        # Videomixer
        self.bin = "" if Args.no_bins else """
            bin.(
                name=blinder
                """

        self.bin += """
                compositor
                    name=compositor-blinder-mix
                ! queue
                    max-size-time=3000000000
                    name=queue-video-mix-blinded
                ! tee
                    name=video-mix-blinded

                video-mix.
                ! queue
                    max-size-time=3000000000
                    name=queue-video-mix-compositor-blinder-mix
                ! compositor-blinder-mix.
            """.format(
                vcaps=self.vcaps,
            )

        if Config.getSlidesSource():
            # add slides compositor
            self.bin += """
                compositor
                    name=compositor-blinder-{name}
                ! queue
                    max-size-time=3000000000
                    name=queue-video-{name}-blinded
                ! tee
                    name=video-{name}-blinded

                video-{name}.
                ! queue
                    max-size-time=3000000000
                    name=queue-video-{name}-compositor-blinder-{name}
                ! compositor-blinder-{name}.
                """.format(
                    name=Config.getSlidesSource()
                )

        for name in self.names:
            # Source from the named Blank-Video
            self.bin += """
                video-blinder-{name}.
                ! queue
                    max-size-time=3000000000
                    name=queue-video-blinder-{name}-compositor-blinder-mix
                ! compositor-blinder-mix.
                """.format(
                    name=name
                )

            if Config.getSlidesSource():
                self.bin += """
                    video-blinder-{name}.
                    ! queue
                        max-size-time=3000000000
                        name=queue-video-blinder-{name}-compositor-blinder-{name}
                    ! compositor-blinder-{slides}.
                    """.format(
                        name=name,
                        slides=Config.getSlidesSource()
                    )

        # Audiomixer
        self.bin += """
            audiomixer
                name=audiomixer-blinder
            ! queue
                max-size-time=3000000000
            ! tee
                name=audio-mix-blinded

            audio-mix.
            ! queue
                max-size-time=3000000000
            ! capssetter caps={acaps}
            ! queue
                max-size-time=3000000000
                name=queue-audiomixer-blinder
            ! audiomixer-blinder.
            """.format(acaps=self.acaps)

        # Source from the Blank-Audio-Tee into the Audiomixer
        self.bin += """
            audio-blinder.
            ! queue
                max-size-time=3000000000
                name=queue-audio-blinded-audiomixer-blinder
            ! audiomixer-blinder.
            """

        self.bin += "" if Args.no_bins else "\n)\n"

        self.blind_source = 0 if len(self.names) > 0 else None

    def __str__(self):
        return 'Blinder[{}]'.format(','.join(self.names))

    def attach(self,pipeline):
        self.pipeline = pipeline
        self.applyMixerState()

    def applyMixerState(self):
        self.applyMixerStateVideo('compositor-blinder-mix')
        if Config.getSlidesSource():
            self.applyMixerStateVideo('compositor-blinder-{}'.format(Config.getSlidesSource()))
        self.applyMixerStateAudio('audiomixer-blinder')

    def applyMixerStateVideo(self, mixername):
        mixer = self.pipeline.get_by_name(mixername)
        if not mixer:
            self.log.error("Video mixer '%s' not found", mixername)
        else:
            mixer.get_static_pad('sink_0').set_property('alpha', int(self.blind_source is None))
            for idx, name in enumerate(self.names):
                blinder_pad = mixer.get_static_pad('sink_%u' % (idx + 1))
                blinder_pad.set_property('alpha', int(self.blind_source == idx))

    def applyMixerStateAudio(self, mixername):
        mixer = self.pipeline.get_by_name(mixername)
        if not mixer:
            self.log.error("Audio mixer '%s' not found", mixername)
        else:
            mixer.get_static_pad('sink_0').set_property('volume', 1.0 if self.blind_source is None else 0.0)
            mixer.get_static_pad('sink_1').set_property('volume', 0.0 if self.blind_source is None else 1.0)

    def setBlindSource(self, source):
        self.blind_source = source
        self.applyMixerState()
