#!/usr/bin/env python3
import logging
from configparser import NoOptionError, NoSectionError

from lib.config import Config
from lib.errors.configuration_error import ConfigurationError

class AudioMix(object):

    def __init__(self):
        self.log = logging.getLogger('AudioMix')

        self.caps = Config.get('mix', 'audiocaps')
        self.names = Config.getlist('mix', 'sources')
        self.log.info('Configuring Mixer for %u Sources', len(self.names))

        # initialize all sources to silent
        self.volumes = [0.0] * len(self.names)

        is_configured = False

        # try per-source volume-setting
        for index, name in enumerate(self.names):
            section = 'source.{}'.format(name)
            try:
                volume = Config.getfloat(section, 'volume')
                self.log.info('Setting Volume of Source %s to %0.2f',
                              name, volume)
                self.volumes[index] = volume
                is_configured = True
            except (NoSectionError, NoOptionError):
                pass

        # try [mix]audiosource shortcut
        try:
            name = Config.get('mix', 'audiosource')
            if is_configured:
                raise ConfigurationError(
                    'cannot configure [mix]audiosource-shortcut and '
                    '[source.*]volume at the same time')

            if name not in self.names:
                raise ConfigurationError(
                    'unknown source configured as [mix]audiosource: %s', name)

            index = self.names.index(name)
            self.log.info('Setting Volume of Source %s to %0.2f', name, 1.0)
            self.volumes[index] = 1.0
            is_configured = True
        except NoOptionError:
            pass

        if is_configured:
            self.log.info(
                'Volume was configured, advising ui not to show a selector')
            Config.add_section_if_missing('audio')
            Config.set('audio', 'volumecontrol', 'false')

        else:
            self.log.info('Setting Volume of first Source %s to %0.2f',
                          self.names[0], 1.0)
            self.volumes[0] = 1.0

        self.bin = """
bin.(
    name=AudioMix
        """

        for audiostream in range(0, Config.getint('mix', 'audiostreams')):
            self.bin +="""
    audiomixer
        name=audiomixer-{audiostream}
    ! tee
        name=audio-mix-{audiostream}
            """.format(
                audiostream=audiostream,
            )

            for idx, name in enumerate(self.names):
                self.bin += """
    audio-{name}-{audiostream}.
    ! queue
        name=queue-audio-{name}-{audiostream}
    ! audiomixer-{audiostream}.
                """.format(
                    name=name,
                    audiostream=audiostream,
                )
        self.bin += ")"


    def attach(self, pipeline):
        self.pipeline = pipeline
        self.updateMixerState()

    def __str__(self):
        return 'AudioMix'

    def updateMixerState(self):
        self.log.info('Updating Mixer-State')

        for idx, name in enumerate(self.names):
            volume = self.volumes[idx]

            self.log.debug('Setting Mixerpad %u to volume=%0.2f', idx, volume)
            for audiostream in range(0, Config.getint('mix', 'audiostreams')):
                mixer = self.pipeline.get_by_name(
                    'audiomixer-{}'.format(audiostream))

                mixerpad = mixer.get_static_pad('sink_%u' % idx)
                mixerpad.set_property('volume', volume)

    def setAudioSource(self, source):
        self.volumes = [float(idx == source) for idx in range(len(self.names))]
        self.updateMixerState()

    def setAudioSourceVolume(self, source, volume):
        self.volumes[source] = volume
        self.updateMixerState()

    def getAudioVolumes(self):
        return self.volumes
