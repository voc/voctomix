#!/usr/bin/env python3
import logging

from lib.args import Args
from lib.config import Config
from lib.tcpmulticonnection import TCPMultiConnection


class AVRawOutput(TCPMultiConnection):

    def __init__(self, source, port, use_audio_mix=False):
        # create logging interface
        self.log = logging.getLogger('AVRawOutput[{}]'.format(source))

        # initialize super
        super().__init__(port)

        # remember things
        self.source = source

        # open bin
        self.bin = "" if Args.no_bins else """
            bin.(
                name=AVRawOutput-{source}
                """.format(source=self.source)

        # video pipeline
        self.bin += """
                video-{source}.
                ! {vcaps}
                ! queue
                    max-size-time=3000000000
                    name=queue-mux-video-{source}
                ! mux-{source}.
                """.format(source=self.source,
                           vcaps=Config.getVideoCaps())

        # audio pipeline
        if use_audio_mix or source in Config.getAudioSources(internal=True):
            self.bin += """
                {use_audio}audio-{audio_source}.
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
                audio_source="mix-blinded" if use_audio_mix else self.source,
                use_audio="" if use_audio_mix else "source-"
            )

        # playout pipeline
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

        # close bin
        self.bin += "" if Args.no_bins else "\n)\n"

    def audio_channels(self):
        return Config.getNumAudioStreams()

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

        # find fdsink and emit 'add'
        fdsink = self.pipeline.get_by_name("fd-{}".format(self.source))
        fdsink.emit('add', conn.fileno())

        # catch disconnect
        def on_client_fd_removed(multifdsink, fileno):
            if fileno == conn.fileno():
                self.log.debug('fd %u removed from multifdsink', fileno)
                self.close_connection(conn)
        fdsink.connect('client-fd-removed', on_client_fd_removed)

        # catch client-removed
        def on_client_removed(multifdsink, fileno, status):
            # GST_CLIENT_STATUS_SLOW = 3,
            if fileno == conn.fileno() and status == 3:
                self.log.warning('about to remove fd %u from multifdsink '
                                 'because it is too slow!', fileno)
        fdsink.connect('client-removed', on_client_removed)
