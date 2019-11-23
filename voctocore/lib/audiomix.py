#!/usr/bin/env python3
import logging
from configparser import NoOptionError, NoSectionError

from lib.config import Config
from lib.errors.configuration_error import ConfigurationError

class AudioMix(object):

    def __init__(self):
        self.log = logging.getLogger('AudioMix')

        self.sources = Config.getAudioSources()
        self.log.info('Configuring audio mixer for %u sources', len(self.sources))

        # initialize all sources to silent
        self.volumes = [0.0] * len(self.sources)

        # try per-source volume-setting
        for index, source in enumerate(self.sources):
            self.volumes[index] = Config.getVolume(source)
            self.log.info('Setting Volume of Source %s to %0.2f',
                          source, self.volumes[index])

        if self.isConfigured():
            self.log.info(
                'Volume was configured, advising ui not to show a selector')
            Config.setShowVolume(False)
        elif self.sources:
            self.log.info('Setting Volume of first Source %s to %0.2f',
                          self.sources[0], 1.0)
            self.volumes[0] = 1.0
        else:
            self.log.info('No audio capable kind of source found!')

        self.bin = """
bin.(
    name=AudioMix
"""
        self.bin += """
    audiomixer
        name=audiomixer
    ! tee
        name=audio-mix
"""
        for idx, name in enumerate(self.sources):
            self.bin += """
                        audio-{name}.
                        ! queue
                        name=queue-audio-{name}
                        ! audiomixer.
                        """.format(name=name)
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
            mixer = self.pipeline.get_by_name('audiomixer')
            mixerpad = mixer.get_static_pad('sink_%d' % idx)
            mixerpad.set_property('volume', volume)

    def setAudioSource(self, source):
        self.volumes = [float(idx == source)
                        for idx in range(len(self.sources))]
        self.updateMixerState()

    def setAudioSourceVolume(self, source, volume):
        self.volumes[source] = volume
        self.updateMixerState()

    def getAudioVolumes(self):
        return self.volumes
