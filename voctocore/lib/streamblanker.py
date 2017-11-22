import logging

from gi.repository import Gst

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

        self.volume = Config.getfloat('stream-blanker', 'volume')

        # Videomixer
        pipeline = """
            compositor name=vmix !
            {vcaps} !
            queue !
            intervideosink channel=video_stream-blanker_out
        """.format(
            vcaps=self.vcaps,
        )

        # Source from the Main-Mix
        pipeline += """
            intervideosrc channel=video_mix_stream-blanker !
            {vcaps} !
            vmix.
        """.format(
            vcaps=self.vcaps,
        )

        for audiostream in range(0, Config.getint('mix', 'audiostreams')):
            # Audiomixer
            pipeline += """
                audiomixer name=amix_{audiostream} !
                {acaps} !
                queue !
                interaudiosink
                    channel=audio_stream-blanker_out_stream{audiostream}
            """.format(
                acaps=self.acaps,
                audiostream=audiostream,
            )

            # Source from the Main-Mix
            pipeline += """
                interaudiosrc
                    channel=audio_mix_stream{audiostream}_stream-blanker !
                {acaps} !
                amix_{audiostream}.
            """.format(
                acaps=self.acaps,
                audiostream=audiostream,
            )

            pipeline += "\n\n"

        # Source from the Blank-Audio into a tee
        pipeline += """
            interaudiosrc channel=audio_stream-blanker_stream0 !
            {acaps} !
            queue !
            tee name=atee
        """.format(
            acaps=self.acaps,
        )

        for audiostream in range(0, Config.getint('mix', 'audiostreams')):
            # Source from the Blank-Audio-Tee into the Audiomixer
            pipeline += """
                atee. ! queue ! amix_{audiostream}.
            """.format(
                audiostream=audiostream,
            )

        pipeline += "\n\n"

        for name in self.names:
            # Source from the named Blank-Video
            pipeline += """
                intervideosrc channel=video_stream-blanker-{name} !
                {vcaps} !
                vmix.
        """.format(
                name=name,
                vcaps=self.vcaps,
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
        is_blanked = self.blankSource is not None

        for audiostream in range(0, Config.getint('mix', 'audiostreams')):
            mixer = self.mixingPipeline.get_by_name(
                'amix_{}'.format(audiostream))
            mixpad = mixer.get_static_pad('sink_0')
            blankpad = mixer.get_static_pad('sink_1')

            mixpad.set_property(
                'volume',
                0.0 if is_blanked else 1.0)

            blankpad.set_property(
                'volume',
                self.volume if is_blanked else 0.0)

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
