#!/usr/bin/env python3
import logging

from lib.args import Args
from lib.config import Config
from lib.tcpmulticonnection import TCPMultiConnection


class AVRawOutput(TCPMultiConnection):

    def __init__(self, source, port, has_audio=True, use_audio_mix=False):
        self.log = logging.getLogger('AVRawOutput[{}]'.format(source))
        super().__init__(port)

        self.source = source

        self.bin = "" if Args.no_bins else """
            bin.(
                name=AVRawOutput-{source}
                """.format(source=self.source)

        self.bin += """
                video-{source}.
                ! queue
                    max-size-time=3000000000
                    name=queue-mux-video-{source}
                ! mux-{source}.
            """.format(
            source=self.source
        )

        # audio pipeline
        if source in Config.getAudioSources(internal=True):
            self.bin += """
                {use_audio}audio-{source}.
                ! queue
                    max-size-time=3000000000
                    name=queue-audio-mix-convert-{source}
                ! audioconvert
                ! queue
                    max-size-time=3000000000
                    name=queue-mux-audio-{source}
                ! mux-{source}.
                """.format(
                source=self.source,
                use_audio="" if use_audio_mix else "source-",
                blinded="-blinded" if Config.getBlinderEnabled() else "")

        self.bin += """
            matroskamux
                name=mux-{source}
                streamable=true
                writing-app=Voctomix-AVRawOutput
            ! queue
                max-size-time=3000000000
                name=queue-fd-{source}
            ! multifdsink
                blocksize=1048576
                buffers-max={buffers_max}
                sync-method=next-keyframe
                name=fd-{source}
            """.format(
            buffers_max=Config.getOutputBuffers(self.source),
            source=self.source
        )
        self.bin += "" if Args.no_bins else "\n)"

    def audio_channels(self):
        return Config.getNumAudioStreams() if self.has_audio else 0

    def video_channels(self):
        return 1

    def is_input(self):
        return False

    def __str__(self):
        return 'AVRawOutput[{}]'.format(self.source)

    def attach(self, pipeline):
        self.pipeline = pipeline

    def on_accepted(self, conn, addr):
        self.log.debug('Adding fd %u to multifdsink', conn.fileno())
        fdsink = self.pipeline.get_by_name(
            "fd-{source}".format(
                source=self.source
            ))
        fdsink.emit('add', conn.fileno())

        def on_disconnect(multifdsink, fileno):
            if fileno == conn.fileno():
                self.log.debug('fd %u removed from multifdsink', fileno)
                self.close_connection(conn)

        def on_about_to_disconnect(multifdsink, fileno, status):
            # GST_CLIENT_STATUS_SLOW = 3,
            if fileno == conn.fileno() and status == 3:
                self.log.warning('about to remove fd %u from multifdsink '
                                 'because it is too slow!', fileno)

        fdsink.connect('client-fd-removed', on_disconnect)
        fdsink.connect('client-removed', on_about_to_disconnect)
