import logging
from gi.repository import Gst

from lib.config import Config
from lib.sources.avsource import AVSource
from lib.tcpsingleconnection import TCPSingleConnection

ALL_AUDIO_CAPS = Gst.Caps.from_string('audio/x-raw')
ALL_VIDEO_CAPS = Gst.Caps.from_string('video/x-raw')


class TCPAVSource(AVSource, TCPSingleConnection):

    def __init__(self, name, port, outputs=None,
                 has_audio=True, has_video=True):
        self.log = logging.getLogger('TCPAVSource[{}]'.format(name))
        AVSource.__init__(self, name, outputs, has_audio, has_video)
        TCPSingleConnection.__init__(self, port)

    def __str__(self):
        return 'TCPAVSource[{name}] on tcp-port {port}'.format(
            name=self.name,
            port=self.boundSocket.getsockname()[1]
        )

    def on_accepted(self, conn, addr):
        pipeline = """
            fdsrc fd={fd} blocksize=1048576 !
            queue !
            matroskademux name=demux
        """.format(
            fd=conn.fileno()
        )
        self.build_pipeline(pipeline, aelem='demux', velem='demux')

        self.audio_caps = Gst.Caps.from_string(Config.get('mix', 'audiocaps'))
        self.video_caps = Gst.Caps.from_string(Config.get('mix', 'videocaps'))

        demux = self.pipeline.get_by_name('demux')
        demux.connect('pad-added', self.on_pad_added)

        self.pipeline.set_state(Gst.State.PLAYING)

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
