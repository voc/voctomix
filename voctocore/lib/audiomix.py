#!/usr/bin/env python3
import logging
from gi.repository import Gst

from vocto.audio_streams import AudioStreams
from voctocore.lib.config import Config
from voctocore.lib.errors.configuration_error import ConfigurationError
from voctocore.lib.args import Args


class AudioMix(object):
    log: logging.Logger
    audio_streams: AudioStreams
    streams: list[str]
    volumes: list[float]
    mix_volume: float
    bin: str
    pipeline: Gst.Pipeline

    def __init__(self):
        self.log = logging.getLogger('AudioMix')

        self.audio_streams = Config.getAudioStreams()
        self.streams = self.audio_streams.get_stream_names()
        # initialize all sources to silent
        self.volumes = [1.0] * len(self.streams)

        self.log.info('Configuring audio mixer for %u streams',
                      len(self.streams))

        self.mix_volume = 1.0

        self.bin = "" if Args.no_bins else """
            bin.(
                name=AudioMix
            """

        matrix = Config.getAudioMixMatrix()
        self.bin += """
            audiomixer
                name=audiomixer
            ! queue
                max-size-time=3000000000
                name=queue-audiomixer-audiomixmatrix
            ! audiomixmatrix
                name=audiomixer-audiomixmatrix
                in_channels={in_channels}
                out_channels={out_channels}
                matrix="{matrix}"
            ! queue
                max-size-time=3000000000
                name=queue-audio-mix
            ! tee
                name=audio-mix
            """.format(in_channels=len(matrix[0]),
                       out_channels=len(matrix),
                       matrix=str(matrix).replace("[","<").replace("]",">"))

        for stream in self.streams:
            self.bin += """
                audio-{stream}.
                ! queue
                    max-size-time=3000000000
                    name=queue-audio-{stream}
                ! audiomixer.
                """.format(stream=stream)
        self.bin += "" if Args.no_bins else "\n)"

    def attach(self, pipeline):
        self.pipeline = pipeline
        self.updateMixerState()

    def __str__(self):
        return 'AudioMix'

    def isConfigured(self):
        for v in self.volumes:
            if v > 0.0:
                return True
        return False

    def updateMixerState(self):
        self.log.info('Updating mixer state')

        for idx, name in enumerate(self.streams):
            volume = self.volumes[idx] * self.mix_volume

            self.log.debug('Setting stream %s to volume=%0.2f', name, volume)
            mixer = self.pipeline.get_by_name('audiomixer')
            mixerpad = mixer.get_static_pad('sink_%d' % idx)
            mixerpad.set_property('volume', volume)

    def setAudioSource(self, source):
        self.volumes = [float(idx == source)
                        for idx in range(len(self.streams))]
        self.updateMixerState()

    def setAudioSourceVolume(self, stream, volume):
        self.volumes[stream] = volume
        self.updateMixerState()

    def setAudioVolume(self, volume):
        self.mix_volume = volume
        self.updateMixerState()

    def getAudioVolumes(self):
        return self.volumes
