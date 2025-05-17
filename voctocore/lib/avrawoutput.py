#!/usr/bin/env python3
import logging
import socket

from gi.repository import Gst

from voctocore.lib.args import Args
from voctocore.lib.avnode import AVIONode
from voctocore.lib.config import Config
from voctocore.lib.tcpmulticonnection import TCPMultiConnection


class AVRawOutput(TCPMultiConnection, AVIONode):
    log: logging.Logger
    source: str
    bin: str

    def __init__(self, source: str, port: int, use_audio_mix: bool=False, audio_blinded: bool=False):
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
        if source in Config.getVideoSources(internal=True):
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
                {use_audio}audio-{audio_source}{audio_blinded}.
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
                audio_source="mix" if use_audio_mix else self.source,
                audio_blinded="-blinded" if audio_blinded else ""
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

    def audio_channels(self) -> int:
        return Config.getNumAudioStreams()

    def video_channels(self) -> int:
        return 1

    def is_input(self) -> bool:
        return False

    def __str__(self) -> str:
        return 'AVRawOutput[{}]'.format(self.source)

    def attach(self, pipeline: Gst.Pipeline):
        self.pipeline = pipeline

    def on_accepted(self, conn: socket.socket, addr: tuple[str, int]):
        self.log.debug('Adding fd %u to multifdsink', conn.fileno())

        # find fdsink and emit 'add'
        fdsink = self.pipeline.get_by_name("fd-{}".format(self.source))
        if fdsink is None:
            raise Exception("could not find pipeline element for {}".format(self))
        fdsink.emit('add', conn.fileno())

        # catch disconnect
        def on_client_fd_removed(multifdsink: Gst.Element, fileno: int):
            if fileno == conn.fileno():
                self.log.debug('fd %u removed from multifdsink', fileno)
                self.close_connection(conn)
        fdsink.connect('client-fd-removed', on_client_fd_removed)

        # catch client-removed
        def on_client_removed(multifdsink: Gst.Element, fileno: int, status: int):
            # GST_CLIENT_STATUS_SLOW = 3,
            if fileno == conn.fileno() and status == 3:
                self.log.warning('about to remove fd %u from multifdsink '
                                 'because it is too slow!', fileno)
        fdsink.connect('client-removed', on_client_removed)
