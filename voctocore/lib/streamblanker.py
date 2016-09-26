import logging
from gi.repository import Gst
from enum import Enum

from lib.config import Config
from lib.clock import Clock


class StreamBlanker(object):
    log = logging.getLogger('StreamBlanker')

    def __init__(self):
        self.acaps = Config.get('mix', 'audiocaps')
        self.vcaps = Config.get('mix', 'videocaps')

        self.names = Config.getlist('stream-blanker', 'sources')
        self.log.info('Configuring StreamBlanker video %u Sources',
                      len(self.names))

        pipeline = """
            compositor name=vmix !
            {vcaps} !
            queue !
            intervideosink channel=video_streamblanker_out

            audiomixer name=amix !
            {acaps} !
            queue !
            interaudiosink channel=audio_streamblanker_out


            intervideosrc channel=video_mix_streamblanker !
            {vcaps} !
            vmix.

            interaudiosrc channel=audio_mix_streamblanker !
            {acaps} !
            amix.


            interaudiosrc channel=audio_streamblanker !
            {acaps} !
            amix.
        """.format(
            acaps=self.acaps,
            vcaps=self.vcaps
        )

        for name in self.names:
            pipeline += """
                intervideosrc channel=video_{name}_streamblanker !
                {vcaps} !
                vmix.
            """.format(
                name=name,
                vcaps=self.vcaps
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
        self.blankSource = None
        self.applyMixerState()

        self.log.debug('Launching Mixing-Pipeline')
        self.mixingPipeline.set_state(Gst.State.PLAYING)

    def on_eos(self, bus, message):
        self.log.debug('Received End-of-Stream-Signal on Mixing-Pipeline')

    def on_error(self, bus, message):
        self.log.debug('Received Error-Signal on Mixing-Pipeline')
        (error, debug) = message.parse_error()
        self.log.debug('Error-Details: #%u: %s', error.code, debug)

    def applyMixerState(self):
        self.applyMixerStateAudio()
        self.applyMixerStateVideo()

    def applyMixerStateAudio(self):
        mixpad = (self.mixingPipeline.get_by_name('amix')
                                     .get_static_pad('sink_0'))
        blankpad = (self.mixingPipeline.get_by_name('amix')
                                       .get_static_pad('sink_1'))

        mixpad.set_property('volume', int(self.blankSource is None))
        blankpad.set_property('volume', int(self.blankSource is not None))

    def applyMixerStateVideo(self):
        mixpad = (self.mixingPipeline.get_by_name('vmix')
                                     .get_static_pad('sink_0'))
        mixpad.set_property('alpha', int(self.blankSource is None))

        for idx, name in enumerate(self.names):
            blankpad = (self.mixingPipeline
                            .get_by_name('vmix')
                            .get_static_pad('sink_%u' % (idx + 1)))
            blankpad.set_property('alpha', int(self.blankSource == idx))

    def setBlankSource(self, source):
        self.blankSource = source
        self.applyMixerState()
