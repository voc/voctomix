#!/usr/bin/env python3
import logging
from abc import ABCMeta, abstractmethod
from gi.repository import GLib

from lib.config import Config
from lib.args import Args


class AVSource(object, metaclass=ABCMeta):

    def __init__(
        self,
        class_name,
        name,
        has_audio=True,
        has_video=True,
        num_streams=None,
        show_no_signal=False,
    ):
        # create logging interface
        self.log = logging.getLogger("%s[%s]" % (class_name, name))

        # make sure we have at least something
        assert has_audio or has_video

        # remember things
        self.class_name = class_name
        self.name = name
        self.has_audio = has_audio
        self.has_video = has_video
        # fetch audio streams from config (different for blinder source)
        if name == "blinder":
            self.audio_streams = Config.getBlinderAudioStreams()
        else:
            self.audio_streams = Config.getAudioStreams()
        # remember if we shall show no-signal underlay
        self.show_no_signal = show_no_signal and Config.getNoSignal()

        # maybe initialize no signal watch dog
        if self.show_no_signal:
            # check if we have video to show no-signal message
            assert self.has_video
            # set timeout at which we check for signal loss
            GLib.timeout_add(self.timer_resolution * 1000, self.do_timeout)

        # this might get attached to the no-signal compositor's input sink
        self.noSignalSink = None

    @abstractmethod
    def __str__(self):
        raise NotImplementedError('__str__ not implemented for this source')

    def attach(self, pipeline):
        if self.show_no_signal:
            # attach self.noSignalSink to no-signal compositor
            self.noSignalSink = pipeline.get_by_name(
                'compositor-{}'.format(self.name)
            ).get_static_pad('sink_1')

    def build_pipeline(self):
        # open enveloping <bin>
        self.bin = (
            ""
            if Args.no_bins
            else """
            bin.(
                name={class_name}-{name}
            """.format(
                class_name=self.class_name, name=self.name
            )
        )

        # attach the pipeline which produces the source
        self.bin += self.build_source()

        # only add audio part if we are using audio
        if self.internal_audio_channels():
            # get port name for audio from source
            audioport = self.build_audioport()
            # check if we have any audio ports from source at all
            if audioport:
                audio_stream_names = self.audio_streams.get_stream_names(self.name)
                self.bin += """
                    {audioport}
                    ! queue
                        max-size-time=3000000000
                        name=queue-source-audio-{name}
                    ! tee
                        name=source-audio-{name}
                    """.format(
                    audioport=audioport, name=self.name
                )
                if not audio_stream_names:
                    self.bin += """
                        source-audio-{name}.
                        ! queue
                            max-size-time=3000000000
                            name=queue-source-audio-fakesink-{name}
                        ! fakesink
                            async=false
                        """.format(
                        name=self.name
                    )
                else:
                    for stream in audio_stream_names:
                        self.log.info(
                            "Creating audio streams '{}' from source '{}'".format(
                                stream, self.name
                            )
                        )
                        self.bin += """
                            source-audio-{name}.
                            ! queue
                                max-size-time=3000000000
                                name=queue-audiomixmatrix-{stream}
                            ! audiomixmatrix
                                name=audiomixmatrix-{stream}
                                in-channels={in_channels}
                                out-channels={out_channels}
                                matrix="{matrix}"
                            ! {acaps}
                            ! queue
                                name=queue-audio-{stream}
                                max-size-time=3000000000
                            ! tee
                                name=audio-{stream}
                            """.format(
                            in_channels=self.internal_audio_channels(),
                            out_channels=Config.getAudioChannels(),
                            matrix=str(
                                self.audio_streams.matrix(
                                    self.name,
                                    stream,
                                    Config.getAudioChannels(),
                                    grid=self.get_valid_channel_numbers(),
                                )
                            )
                            .replace("[", "<")
                            .replace("]", ">"),
                            acaps=Config.getAudioCaps(),
                            stream=stream,
                            name=self.name,
                        )

        if self.has_video:
            if self.show_no_signal and Config.getNoSignal():
                video = """
                    videotestsrc
                        name=canvas-{name}
                        pattern={nosignalpattern}
                    ! textoverlay
                        name=nosignal-{name}
                        text=\"{nosignal}\"
                        valignment=center
                        halignment=center
                        shaded-background=yes
                        font-desc="Roboto Bold, 20"
                    ! {vcaps}
                    ! queue
                        max-size-time=3000000000
                    ! compositor-{name}.

                    {videoport}
                    ! {vcaps}
                    ! queue
                        max-size-time=3000000000
                    ! compositor-{name}.

                    compositor
                        name=compositor-{name}
                    ! queue
                        max-size-time=3000000000
                    ! tee
                        name=video-{name}"""
            else:
                video = """
                    {videoport}
                    ! {vcaps}
                    ! queue
                        max-size-time=3000000000
                    ! tee
                        name=video-{name}"""
            self.bin += video.format(
                videoport=self.build_videoport(),
                name=self.name,
                vcaps=Config.getVideoCaps(),
                nosignal=self.get_nosignal_text(),
                nosignalpattern=Config.getNoSignal(),
            )
        self.bin += (
            ""
            if Args.no_bins
            else """
                    )
                    """
        )

        self.bin = self.bin

    def build_source(self):
        return ""

    def build_deinterlacer(self):
        source_mode = Config.getSourceScan(self.name)

        if source_mode == "interlaced":
            return "videoconvert ! yadif mode=interlaced"
        elif source_mode == "psf":
            return "capssetter " "caps=video/x-raw,interlace-mode=progressive"
        elif source_mode == "progressive":
            return None
        else:
            raise RuntimeError(
                "Unknown Deinterlace-Mode on source {} configured: {}".format(
                    self.name, source_mode
                )
            )

    def video_channels(self):
        return 1 if self.has_video else 0

    def audio_channels(self):
        return self.audio_streams.num_channels(self.name) if self.has_audio else 0

    def internal_audio_channels(self):
        return (
            self.audio_streams.num_channels(self.name, self.get_valid_channel_numbers())
            if self.has_audio
            else 0
        )

    def get_valid_channel_numbers(self):
        return [x for x in range(1, 255)]

    def num_connections(self):
        return 0

    def is_input(self):
        return True

    def section(self):
        return 'source.{}'.format(self.name)

    @abstractmethod
    def port(self):
        raise NotImplementedError("port() not implemented in %s" % self.name)

    def build_audioport(self):
        raise None

    def build_videoport(self):
        raise None

    def get_nosignal_text(self):
        return "NO SIGNAL\n" + self.name.upper()

    def do_timeout(self):
        if self.noSignalSink:
            self.noSignalSink.set_property(
                'alpha', 1.0 if self.num_connections() > 0 else 0.0
            )
        # just come back
        return True
