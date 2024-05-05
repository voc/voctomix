#!/usr/bin/env python3
import logging

from gi.repository import Gst, GObject
import socket

from lib.config import Config
from lib.sources.avsource import AVSource

ALL_AUDIO_CAPS = Gst.Caps.from_string('audio/x-raw')
ALL_VIDEO_CAPS = Gst.Caps.from_string('video/x-raw')


class TCPAVSource(AVSource):
    timer_resolution = 0.5

    def __init__(
        self, name, listen_port, has_audio=True, has_video=True, force_num_streams=None
    ):
        super().__init__(
            'TCPAVSource',
            name,
            has_audio,
            has_video,
            force_num_streams,
            show_no_signal=True,
        )

        self.listen_port = listen_port
        self.tcpsrc = None
        self.audio_caps = Gst.Caps.from_string(Config.getAudioCaps())
        self.video_caps = Gst.Caps.from_string(Config.getVideoCaps())
        self.build_pipeline()
        self.connected = False

    def port(self):
        return "%s:%d" % (socket.gethostname(), self.listen_port)

    def num_connections(self):
        if self.connected:
            return 1
        else:
            return 0

    def attach(self, pipeline):
        super().attach(pipeline)
        self.log.debug("connecting to pads")

        # create probe at static tcpserversrc.src to get EOS and trigger a restart
        self.tcpsrc = pipeline.get_by_name('tcpsrc-{name}'.format(name=self.name))
        self.tcpsrc.get_static_pad("src").add_probe(
            Gst.PadProbeType.EVENT_DOWNSTREAM | Gst.PadProbeType.BLOCK,
            self.on_pad_event,
        )

        # subscribe to creation of dynamic pads in matroskademux
        self.demux = pipeline.get_by_name('demux-{name}'.format(name=self.name))
        self.demux.connect('pad-added', self.on_pad_added)

        # remember queues the demux is connected to to reconnect them when necessary
        self.queue_audio = pipeline.get_by_name(
            'queue-tcpsrc-audio-{name}'.format(name=self.name)
        )
        self.queue_video = pipeline.get_by_name(
            'queue-tcpsrc-video-{name}'.format(name=self.name)
        )

        self.src = pipeline.get_by_name('src-{name}'.format(name=self.name))

    def __str__(self):
        return 'TCPAVSource[{name}] listening at {listen} ({port})'.format(
            name=self.name,
            listen=self.port(),
            port=(
                self.tcpsrc.get_property("current-port")
                if self.tcpsrc
                else "<disconnected>"
            ),
        )

    def build_source(self):
        deinterlacer = self.build_deinterlacer()
        pipe = """
            tcpserversrc
                name=tcpsrc-{name}
                do-timestamp=TRUE
                port={port}
            ! demux-{name}.

            matroskademux
                name=demux-{name}
            """.format(
            name=self.name, port=self.listen_port
        )

        if deinterlacer:
            pipe += """
                demux-{name}.video_0
                ! queue
                    max-size-time=3000000000
                    name=queue-tcpsrc-video-{name}
                ! video/x-raw
                ! {deinterlacer}""".format(
                name=self.name, deinterlacer=deinterlacer
            )
        return pipe

    def build_deinterlacer(self):
        deinterlacer = super().build_deinterlacer()
        if deinterlacer:
            return deinterlacer + ' name=deinter-{name}'.format(name=self.name)
        else:
            return None

    def on_pad_added(self, demux, pad):
        caps = pad.query_caps(None)
        self.log.debug('demuxer added pad w/ caps: %s', caps.to_string())

        if self.has_audio and caps.can_intersect(ALL_AUDIO_CAPS):
            self.log.debug(
                'new demuxer-pad is an audio-pad, '
                'testing against configured audio-caps'
            )
            if not caps.can_intersect(self.audio_caps):
                self.log.warning(
                    'the incoming connection presented '
                    'an audio-stream that is not compatible '
                    'to the configured caps'
                )
                self.log.warning('   incoming caps:   %s', caps.to_string())
                self.log.warning('   configured caps: %s', self.audio_caps.to_string())

        elif self.has_video and caps.can_intersect(ALL_VIDEO_CAPS):
            self.log.debug(
                'new demuxer-pad is a video-pad, '
                'testing against configured video-caps'
            )
            if not caps.can_intersect(self.video_caps):
                self.log.warning(
                    'the incoming connection presented '
                    'a video-stream that is not compatible '
                    'to the configured caps'
                )
                self.log.warning('   incoming caps:   %s', caps.to_string())
                self.log.warning('   configured caps: %s', self.video_caps.to_string())

            self.test_and_warn_interlace_mode(caps)

        # relink demux with following audio and video queues
        if not pad.is_linked():
            self.demux.link(self.queue_audio)
            self.demux.link(self.queue_video)
        self.connected = True

    def on_pad_event(self, pad, info):
        if info.get_event().type == Gst.EventType.EOS:
            self.log.warning('scheduling source restart')
            self.connected = False
            GObject.idle_add(self.restart)

        return Gst.PadProbeReturn.PASS

    def restart(self):
        self.log.debug('restarting source \'%s\'', self.name)
        self.tcpsrc.set_state(Gst.State.READY)
        self.demux.set_state(Gst.State.READY)
        self.demux.set_state(Gst.State.PLAYING)
        self.tcpsrc.set_state(Gst.State.PLAYING)

    def build_audioport(self):
        return """
    ! queue
        max-size-time=3000000000
        name=queue-{name}.audio""".format(
            name=self.name
        )

    def build_videoport(self):
        deinterlacer = self.build_deinterlacer()
        if deinterlacer:
            return """
    deinter-{name}.""".format(
                name=self.name
            )
        else:
            return """
    demux-{name}.""".format(
                name=self.name
            )

    def test_and_warn_interlace_mode(self, caps):
        interlace_mode = caps.get_structure(0).get_string('interlace-mode')
        source_mode = Config.getSourceScan(self.name)

        if interlace_mode == 'mixed' and source_mode == 'progressive':
            self.log.warning(
                'your source sent an interlace_mode-flag in the matroska-'
                'container, specifying the source-video-stream is of '
                'mixed-mode.\n'
                'this is probably a gstreamer-bug which is triggered with '
                'recent ffmpeg-versions\n'
                'setting [source.{name}] deinterlace=assume-progressive '
                'might help see https://github.com/voc/voctomix/issues/137 '
                'for more information'.format(name=self.name)
            )
