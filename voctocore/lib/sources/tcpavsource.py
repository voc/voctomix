import logging

from gi.repository import Gst

from lib.config import Config
from lib.sources.avsource import AVSource
from lib.tcpsingleconnection import TCPSingleConnection

ALL_AUDIO_CAPS = Gst.Caps.from_string('audio/x-raw')
ALL_VIDEO_CAPS = Gst.Caps.from_string('video/x-raw')


class TCPAVSource(AVSource, TCPSingleConnection):
    def __init__(self, name, port, outputs=None,
                 has_audio=True, has_video=True,
                 force_num_streams=None):
        self.log = logging.getLogger('TCPAVSource[{}]'.format(name))
        AVSource.__init__(self, name, outputs,
                          has_audio, has_video,
                          force_num_streams)
        TCPSingleConnection.__init__(self, port)

    def __str__(self):
        return 'TCPAVSource[{name}] on tcp-port {port}'.format(
            name=self.name,
            port=self.boundSocket.getsockname()[1]
        )

    def on_accepted(self, conn, addr):
        deinterlacer = self.build_deinterlacer()
        pipeline = """
            fdsrc fd={fd} blocksize=1048576 !
            queue !
            matroskademux name=demux
        """.format(
            fd=conn.fileno()
        )

        if deinterlacer:
            pipeline += """
                demux. !
                    video/x-raw !
                    {deinterlacer}
            """.format(
                deinterlacer=self.build_deinterlacer()
            )
            self.build_pipeline(pipeline)

        else:
            self.build_pipeline(pipeline)

        self.audio_caps = Gst.Caps.from_string(Config.get('mix', 'audiocaps'))
        self.video_caps = Gst.Caps.from_string(Config.get('mix', 'videocaps'))

        demux = self.pipeline.get_by_name('demux')
        demux.connect('pad-added', self.on_pad_added)

        self.pipeline.set_state(Gst.State.PLAYING)

    def build_deinterlacer(self):
        deinterlacer = super().build_deinterlacer()

        if deinterlacer != '':
            deinterlacer += ' name=deinter'

        return deinterlacer

    def on_pad_added(self, demux, src_pad):
        caps = src_pad.query_caps(None)
        self.log.debug('demuxer added pad w/ caps: %s', caps.to_string())
        if caps.can_intersect(ALL_AUDIO_CAPS):
            self.log.debug('new demuxer-pad is an audio-pad, '
                           'testing against configured audio-caps')
            if not caps.can_intersect(self.audio_caps):
                self.log.warning('the incoming connection presented '
                                 'an audio-stream that is not compatible '
                                 'to the configured caps')
                self.log.warning('   incoming caps:   %s', caps.to_string())
                self.log.warning('   configured caps: %s',
                                 self.audio_caps.to_string())

        elif caps.can_intersect(ALL_VIDEO_CAPS):
            self.log.debug('new demuxer-pad is a video-pad, '
                           'testing against configured video-caps')
            if not caps.can_intersect(self.video_caps):
                self.log.warning('the incoming connection presented '
                                 'a video-stream that is not compatible '
                                 'to the configured caps')
                self.log.warning('   incoming caps:   %s', caps.to_string())
                self.log.warning('   configured caps: %s',
                                 self.video_caps.to_string())

            self.test_and_warn_interlace_mode(caps)

    def on_eos(self, bus, message):
        super().on_eos(bus, message)
        if self.currentConnection is not None:
            self.disconnect()

    def on_error(self, bus, message):
        super().on_error(bus, message)
        if self.currentConnection is not None:
            self.disconnect()

    def disconnect(self):
        self.pipeline.set_state(Gst.State.NULL)
        self.pipeline = None
        self.close_connection()

    def restart(self):
        if self.currentConnection is not None:
            self.disconnect()

    def build_audioport(self, audiostream):
        return 'demux.audio_{}'.format(audiostream)

    def build_videoport(self):
        deinterlacer = self.build_deinterlacer()
        if deinterlacer:
            return 'deinter.'
        else:
            return 'demux.'

    def test_and_warn_interlace_mode(self, caps):
        interlace_mode = caps.get_structure(0).get_string('interlace-mode')
        deinterlace_config = self.get_deinterlace_config()

        if interlace_mode == 'mixed' and deinterlace_config == 'no':
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
