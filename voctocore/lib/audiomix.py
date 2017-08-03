import logging
from configparser import NoOptionError, NoSectionError

from gi.repository import Gst

from lib.config import Config
from lib.clock import Clock


class AudioMix(object):

    def __init__(self):
        self.log = logging.getLogger('AudioMix')

        self.caps = Config.get('mix', 'audiocaps')
        self.names = Config.getlist('mix', 'sources')
        self.log.info('Configuring Mixer for %u Sources', len(self.names))

        # initialize all sources to silent
        self.volumes = [0.0] * len(self.names)

        # set default audio-source to 1.0
        audiosource = Config.get('mix', 'audiosource', fallback=self.names[0])
        index = self.names.index(audiosource)
        self.log.info('Configuring Mixer-Pad %s (%u) to %f',
                      audiosource, index, 1.0)
        self.volumes[index] = 1.0

        # scan per-source config for volume-setting
        for index, name in enumerate(self.names):
            section = 'source.{}'.format(name)
            try:
                volume = Config.getfloat(section, 'volume')
                self.log.info('Configuring Mixer-Pad %s (%u) to %f',
                              name, index, volume)
                self.volumes[index] = volume
            except (NoSectionError, NoOptionError):
                pass

        pipeline = """
            audiomixer name=mix !
            {caps} !
            queue !
            tee name=tee

            tee. ! queue ! interaudiosink channel=audio_mix_out
        """.format(
            caps=self.caps
        )

        if Config.getboolean('previews', 'enabled'):
            pipeline += """
                tee. ! queue ! interaudiosink channel=audio_mix_preview
            """

        if Config.getboolean('stream-blanker', 'enabled'):
            pipeline += """
                tee. ! queue ! interaudiosink channel=audio_mix_stream-blanker
            """

        for idx, name in enumerate(self.names):
            pipeline += """
                interaudiosrc channel=audio_{name}_mixer !
                {caps} !
                mix.
            """.format(
                name=name,
                caps=self.caps
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
            mixerpad = (self.mixingPipeline.get_by_name('mix')
                                           .get_static_pad('sink_%u' % idx))
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
