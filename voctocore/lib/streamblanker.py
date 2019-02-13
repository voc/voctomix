#!/usr/bin/env python3
import logging

from gi.repository import Gst

from lib.config import Config
from lib.clock import Clock
from lib.args import Args


class StreamBlanker(object):
    log = logging.getLogger('StreamBlanker')

    def __init__(self):
        self.acaps = Config.getAudioCaps()
        self.vcaps = Config.getVideoCaps()

        self.names = Config.getStreamBlankerSources()
        self.log.info('Configuring StreamBlanker video %u Sources',
                      len(self.names))

        self.volume = Config.getStreamBlankerVolume()

        # Videomixer
        self.bin = """
bin.(
    name=streamblanker

    compositor
        name=videomixer-sb
    ! tee
        name=video-mix-sb

    video-mix.
    ! queue
        name=queue-video-mix-videomixer-sb
    ! videomixer-sb.
        """.format(
            vcaps=self.vcaps,
        )

        if Config.getSlidesSource():
            # add slides compositor
            self.bin += """
    compositor
        name=videomixer-sb-slides
    ! tee
        name=video-mix-sb-slides

    video-mix.
    ! queue
        name=queue-videomixer-sb-slides
    ! videomixer-sb-slides.
            """

        for name in self.names:
            # Source from the named Blank-Video
            self.bin += """
    video-sb-{name}.
    ! queue
        name=queue-video-sb-{name}
    ! videomixer-sb.
            """.format(
                name=name
            )

            if Config.getSlidesSource():
                self.bin += """
    video-sb-{name}.
    ! queue
        name=queue-video-sb-slides-{name}
    ! videomixer-sb-slides.
                """.format(
                    name=name,
                )

        for audiostream in range(0, Config.getNumAudioStreams()):
            # Audiomixer
            self.bin += """
    audiomixer
        name=audiomixer-sb-{audiostream}
    ! tee
        name=audio-mix-sb-{audiostream}
    ! tee
        name=audio-mix-sb-slides-{audiostream}

    audio-mix-{audiostream}.
    ! queue
        name=queue-audio-mix-{audiostream}
    ! audiomixer-sb-{audiostream}.
            """.format(
                acaps=self.acaps,
                audiostream=audiostream
            )

        for audiostream in range(0, Config.getNumAudioStreams()):
            # Source from the Blank-Audio-Tee into the Audiomixer
            self.bin += """
    audio-sb-{audiostream}.
    ! queue
        name=queue-audio-sb-slides-{audiostream}
    ! audiomixer-sb-{audiostream}.
            """.format(
                audiostream=audiostream,
            )

        self.bin += "\n)\n"

        self.blankSource = 0 if len(self.names) > 0 else None

    def __str__(self):
        return 'StreamBlanker[{}]'.format(','.join(self.names))

    def attach(self,pipeline):
        self.pipeline = pipeline
        self.applyMixerState()

    def applyMixerState(self):
        self.applyMixerStateVideo('videomixer-sb')
        if Config.getSlidesSource():
            self.applyMixerStateVideo('videomixer-sb-slides')

    def applyMixerStateVideo(self, mixername):
        mixer = self.pipeline.get_by_name(mixername)
        if not mixer:
            self.log.error("Mixer '%s' not found", mixername)
        mixer.get_static_pad('sink_0').set_property('alpha', int(self.blankSource is None))
        blanker = self.pipeline.get_by_name(mixername)
        if not blanker:
            self.log.error("Blanger '%s' not found", mixername)
        for idx, name in enumerate(self.names):
            blankpad = blanker.get_static_pad('sink_%u' % (idx + 1))
            blankpad.set_property('alpha', int(self.blankSource == idx))

    def setBlankSource(self, source):
        self.blankSource = source
        self.applyMixerState()
