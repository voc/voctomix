#!/usr/bin/env python3
import logging
from configparser import NoOptionError, NoSectionError

from lib.config import Config
from lib.errors.configuration_error import ConfigurationError
from lib.args import Args


class AudioMix(object):

    def __init__(self):
        self.log = logging.getLogger('AudioMix')

        self.audio_streams = Config.getAudioStreams()
        self.streams = self.audio_streams.get_stream_names()
        # initialize all sources to silent
        self.volumes = [0.0] * len(self.streams)

        self.log.info('Configuring audio mixer for %u streams',
                      len(self.streams))

        # try per-source volume-setting
        for index, stream in enumerate(self.streams):
            self.volumes[index] = Config.getVolume(stream)
            self.log.info('Setting volume of stream %s to %0.2f',
                          stream, self.volumes[index])

        if self.isConfigured():
            self.log.info(
                'Volume was configured, advising ui not to show a selector')
            Config.setShowVolume(False)
        elif self.audio_streams:
            self.log.info('Setting volume of first stream %s to %0.2f',
                          self.audio_streams[0], 1.0)
            self.volumes[0] = 1.0
        else:
            self.log.info('No audio capable kind of source found!')

        self.mix_volume = 1.0

        self.bin = "" if Args.no_bins else """
            bin.(
                name=AudioMix
            """

        channels = Config.getAudioChannels()

        def identity():
            matrix = [[0.0 for x in range(0, channels)]
                      for x in range(0, channels)]
            for i in range(0, channels):
                matrix[i][i] = 1.0
            return str(matrix).replace("[","<").replace("]",">")

        self.bin += """
            audiomixer
                name=audiomixer
            ! queue
            ! audiomixmatrix
                name=audiomixmatrix
                in_channels={in_channels}
                out_channels={out_channels}
                matrix="{matrix}"
            ! tee
                name=audio-mix
            ! tee
                name=source-audio-mix
            """.format(in_channels=channels,
                       out_channels=channels,
                       matrix=identity())

        for stream in self.streams:
            self.bin += """
                audio-{stream}.
                ! queue
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
                        for idx in range(len(self.sources))]
        self.updateMixerState()

    def setAudioSourceVolume(self, stream, volume):
        if stream == 'mix':
            self.mix_volume = volume
        else:
            self.volumes[stream] = volume
        self.updateMixerState()

    def setAudioVolume(self, volume):
        self.mix_volume = volume
        self.updateMixerState()

    def getAudioVolumes(self):
        return self.volumes
