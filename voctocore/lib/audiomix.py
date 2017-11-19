import logging
from configparser import NoOptionError, NoSectionError

from gi.repository import Gst

from lib.config import Config
from lib.clock import Clock
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

        pipeline = ""
        for audiostream in range(0, Config.getint('mix', 'audiostreams')):
            pipeline += """
                audiomixer name=mix_{audiostream} !
                {caps} !
                queue !
                tee name=tee_{audiostream}

                tee_{audiostream}. ! queue ! interaudiosink
                    channel=audio_mix_out_stream{audiostream}
            """.format(
                caps=self.caps,
                audiostream=audiostream,
            )

            if Config.getboolean('previews', 'enabled'):
                pipeline += """
                    tee_{audiostream}. ! queue ! interaudiosink
                        channel=audio_mix_stream{audiostream}_preview
                """.format(
                    audiostream=audiostream,
                )

            if Config.getboolean('stream-blanker', 'enabled'):
                pipeline += """
                    tee_{audiostream}. ! queue ! interaudiosink
                        channel=audio_mix_stream{audiostream}_stream-blanker
                """.format(
                    audiostream=audiostream,
                )

            for idx, name in enumerate(self.names):
                pipeline += """
                    interaudiosrc
                        channel=audio_{name}_mixer_stream{audiostream} !
                    {caps} !
                    mix_{audiostream}.
                """.format(
                    name=name,
                    caps=self.caps,
                    audiostream=audiostream,
                )

        self.log.debug('Creating Mixing-Pipeline:\n%s', pipeline)
        self.mixingPipeline = Gst.parse_launch(pipeline)
        self.mixingPipeline.use_clock(Clock)

        self.log.debug('Binding Error & End-of-Stream-Signal '
                       'on Mixing-Pipeline')
        self.mixingPipeline.bus.add_signal_watch()
        self.mixingPipeline.bus.connect("message::eos", self.on_eos)
        self.mixingPipeline.bus.connect("message::error", self.on_error)

        self.log.debug('Initializing Mixer-State')
        self.updateMixerState()

        self.log.debug('Launching Mixing-Pipeline')
        self.mixingPipeline.set_state(Gst.State.PLAYING)

    def updateMixerState(self):
        self.log.info('Updating Mixer-State')

        for idx, name in enumerate(self.names):
            volume = self.volumes[idx]

            self.log.debug('Setting Mixerpad %u to volume=%0.2f', idx, volume)
            for audiostream in range(0, Config.getint('mix', 'audiostreams')):
                mixer = self.mixingPipeline.get_by_name(
                    'mix_{}'.format(audiostream))

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

    def on_eos(self, bus, message):
        self.log.debug('Received End-of-Stream-Signal on Mixing-Pipeline')

    def on_error(self, bus, message):
        self.log.debug('Received Error-Signal on Mixing-Pipeline')
        (error, debug) = message.parse_error()
        self.log.debug('Error-Details: #%u: %s', error.code, debug)
