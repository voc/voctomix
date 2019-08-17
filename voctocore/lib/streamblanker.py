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

        # Audiomixer
        self.bin += """
    audiomixer
        name=audiomixer-sb
    ! tee
        name=audio-mix-sb
    ! tee
        name=audio-mix-sb-slides

    audio-mix.
    ! queue
        name=queue-audio-mix
    ! audiomixer-sb.
            """.format(acaps=self.acaps)

        # Source from the Blank-Audio-Tee into the Audiomixer
        self.bin += """
    audio-sb.
    ! queue
        name=queue-audio-sb
    ! audiomixer-sb.
"""

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
        self.applyMixerStateAudio('audiomixer-sb')

    def applyMixerStateVideo(self, mixername):
        mixer = self.pipeline.get_by_name(mixername)
        if not mixer:
            self.log.error("Video mixer '%s' not found", mixername)
        else:
            mixer.get_static_pad('sink_0').set_property('alpha', int(self.blankSource is None))
            for idx, name in enumerate(self.names):
                blankpad = mixer.get_static_pad('sink_%u' % (idx + 1))
                blankpad.set_property('alpha', int(self.blankSource == idx))

    def applyMixerStateAudio(self, mixername):
        mixer = self.pipeline.get_by_name(mixername)
        if not mixer:
            self.log.error("Audio mixer '%s' not found", mixername)
        else:
            mixer.get_static_pad('sink_0').set_property('volume', 1.0 if self.blankSource is None else 0.0)
            mixer.get_static_pad('sink_1').set_property('volume', 0.0 if self.blankSource is None else 1.0)

    def setBlankSource(self, source):
        self.blankSource = source
        self.applyMixerState()
