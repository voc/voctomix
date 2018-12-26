#!/usr/bin/env python3
import logging

from gi.repository import Gst

from lib.config import Config
from lib.clock import Clock
from lib.args import Args


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
        self.pipe = """
compositor
    name=videomixer-sb
! tee
    name=video-mix-sb
        """.format(
            vcaps=self.vcaps,
        )

        # Source from the Main-Mix
        self.pipe += """
video-mix.
! queue
! videomixer-sb.
        """

        if Config.has_option('mix', 'slides_source_name'):
            self.pipe += """
compositor
    name=videomixer-sb-slides
! tee
    name=video-mix-sb-slides.
            """

            self.pipe += """
video-sb-slides.
! queue
! videomixer-sb-slides.
            """

        for audiostream in range(0, Config.getint('mix', 'audiostreams')):
            # Audiomixer
            self.pipe += """
audiomixer
    name=audiomixer-sb-{audiostream}
! tee
! audio-mix-sb-{audiostream}.
            """.format(
                acaps=self.acaps,
                audiostream=audiostream
            )
            # Source from the Main-Mix
            self.pipe += """
audio-mix-{audiostream}.
! queue
! audiomixer-sb-{audiostream}.
            """.format(
                audiostream=audiostream
            )

            self.pipe += "\n\n"

        for audiostream in range(0, Config.getint('mix', 'audiostreams')):
            # Source from the Blank-Audio-Tee into the Audiomixer
            self.pipe += """
audio-sb-{audiostream}.
! queue
! audiomixer-sb-{audiostream}.
            """.format(
                audiostream=audiostream,
            )

        self.pipe += "\n\n"

        for name in self.names:
            # Source from the named Blank-Video
            self.pipe += """
video-sb-{name}.
! queue
! videomixer-sb.
            """.format(
                name=name
            )

            if Config.has_option('mix', 'slides_source_name'):
                self.pipe += """
video-sb-{name}.
! queue
! videomixer-sb-slides.
                """.format(
                    name=name,
                )

        self.blankSource = 0 if len(self.names) > 0 else None

    def attach(self,pipeline):
        self.pipeline = pipeline
        self.applyMixerState()

    def on_eos(self, bus, message):
        self.log.debug('Received End-of-Stream-Signal on Mixing-Pipeline')

    def on_error(self, bus, message):
        self.log.error('Received Error-Signal on Mixing-Pipeline')
        (error, debug) = message.parse_error()
        self.log.debug('Error-Details: #%u: %s', error.code, debug)

    def applyMixerState(self):
        self.applyMixerStateAudio()
        self.applyMixerStateVideo('sb-videomixer')
        if Config.has_option('mix', 'slides_source_name'):
            self.applyMixerStateVideo('sb-slides-videomixer')

    def applyMixerStateAudio(self):
        is_blanked = self.blankSource is not None

        for audiostream in range(0, Config.getint('mix', 'audiostreams')):
            mixer = self.pipeline.get_by_name(
                'amix_{}'.format(audiostream))
            mixpad = mixer.get_static_pad('sink_0')
            blankpad = mixer.get_static_pad('sink_1')

            mixpad.set_property(
                'volume',
                0.0 if is_blanked else 1.0)

            blankpad.set_property(
                'volume',
                self.volume if is_blanked else 0.0)

    def applyMixerStateVideo(self, mixername):
        mixpad = (self.pipeline.get_by_name(mixername)
                  .get_static_pad('sink_0'))
        mixpad.set_property('alpha', int(self.blankSource is None))

        for idx, name in enumerate(self.names):
            blankpad = (self.pipeline
                        .get_by_name(mixername)
                        .get_static_pad('sink_%u' % (idx + 1)))
            blankpad.set_property('alpha', int(self.blankSource == idx))

    def setBlankSource(self, source):
        self.blankSource = source
        self.applyMixerState()
