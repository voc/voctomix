#!/usr/bin/env python3
import logging
from configparser import NoOptionError, NoSectionError

from lib.config import Config
from lib.errors.configuration_error import ConfigurationError

class AudioMix(object):

    def __init__(self):
        self.log = logging.getLogger('AudioMix')

        self.sources = Config.getSources()
        self.log.info('Configuring Mixer for %u Sources', len(self.sources))

        # initialize all sources to silent
        self.volumes = [0.0] * len(self.sources)

        # try per-source volume-setting
        for index, source in enumerate(self.sources):
            self.volumes[index] = Config.getVolume(source)
            self.log.info('Setting Volume of Source %s to %0.2f',
                          source, self.volumes[index])

        # try [mix]audiosource shortcut
        source = Config.getAudioSource()
        if source and self.isConfigured():
            raise ConfigurationError(
                'cannot configure [mix]audiosource-shortcut and '
                '[source.*]volume at the same time')

            if source not in self.sources:
                raise ConfigurationError(
                    'unknown source configured as [mix]audiosource: %s', source)

            index = self.sources.index(source)
            self.log.info('Setting Volume of Source %s to %0.2f', source, 1.0)
            self.volumes[index] = 1.0

        if self.isConfigured():
            self.log.info(
                'Volume was configured, advising ui not to show a selector')
            Config.setShowVolume(False)
        else:
            self.log.info('Setting Volume of first Source %s to %0.2f',
                          self.sources[0], 1.0)
            self.volumes[0] = 1.0

        self.bin = """
bin.(
    name=AudioMix
        """

        for audiostream in range(0, Config.getNumAudioStreams()):
            self.bin +="""
    audiomixer
        name=audiomixer-{audiostream}
    ! tee
        name=audio-mix-{audiostream}
            """.format(
                audiostream=audiostream,
            )

            for idx, name in enumerate(self.sources):
                self.bin += """
    audio-{name}-{audiostream}.
    ! queue
        name=queue-audio-{name}-{audiostream}
    ! audiomixer-{audiostream}.
                """.format(
                    name=name,
                    audiostream=audiostream,
                )
        self.bin += "\n)"


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
        self.log.info('Updating Mixer-State')

        for idx, name in enumerate(self.sources):
            volume = self.volumes[idx]

            self.log.debug('Setting Mixerpad %u to volume=%0.2f', idx, volume)
            for audiostream in range(0, Config.getNumAudioStreams()):
                mixer = self.pipeline.get_by_name(
                    'audiomixer-{}'.format(audiostream))

                mixerpad = mixer.get_static_pad('sink_%u' % idx)
                mixerpad.set_property('volume', volume)

    def setAudioSource(self, source):
        self.volumes = [float(idx == source) for idx in range(len(self.sources))]
        self.updateMixerState()

    def setAudioSourceVolume(self, source, volume):
        self.volumes[source] = volume
        self.updateMixerState()

    def getAudioVolumes(self):
        return self.volumes
