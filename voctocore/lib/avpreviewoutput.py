import logging
import socket

from gi.repository import Gst

from vocto.video_codecs import construct_video_encoder_pipeline
from voctocore.lib.avnode import AVIONode

from voctocore.lib.tcpmulticonnection import TCPMultiConnection
from voctocore.lib.config import Config
from voctocore.lib.args import Args

class AVPreviewOutput(TCPMultiConnection, AVIONode):
    log: logging.Logger
    source: str
    bin: str

    def __init__(self, source: str, port: int, use_audio_mix: bool=False, audio_blinded: bool=False):
        # create logging interface
        if not hasattr(self, 'log'):
            self.log = logging.getLogger('AVPreviewOutput[{}]'.format(source))

        # initialize super
        super().__init__(port)

        # remember things
        self.source = source

        # open bin
        self.bin = "" if Args.no_bins else """
            bin.(
                name=AVPreviewOutput-{source}
                """.format(source=self.source)

        # video pipeline
        if source in Config.getVideoSources(internal=True):
            self.bin += """
                    video-{source}.
                    ! {vcaps}
                    ! queue
                        max-size-time=3000000000
                        name=queue-preview-video-{source}
                    {vpipeline}
                    ! queue
                        max-size-time=3000000000
                        name=queue-mux-preview-{source}
                    ! mux-preview-{source}.
                    """.format(source=self.source,
                               vpipeline=construct_video_encoder_pipeline(Config, 'previews'),
                               vcaps=Config.getVideoCaps()
                               )

        # audio pipeline
        if use_audio_mix or source in Config.getAudioSources(internal=True):
            self.bin += """
                    {use_audio}audio-{audio_source}{audio_blinded}.
                    ! queue
                        max-size-time=3000000000
                        name=queue-preview-audio-{source}
                    ! audioconvert
                    ! queue
                        max-size-time=3000000000
                        name=queue-mux-preview-audio-{source}
                    ! mux-preview-{source}.
                    """.format(source=self.source,
                               use_audio="" if use_audio_mix else "source-",
                               audio_source="mix" if use_audio_mix else self.source,
                               audio_blinded="-blinded" if audio_blinded else ""
                               )

        # playout pipeline
        self.bin += """
                matroskamux
                    name=mux-preview-{source}
                    streamable=true
                    writing-app=Voctomix-AVPreviewOutput
                ! queue
                    max-size-time=3000000000
                    name=queue-fd-preview-{source}
                ! multifdsink
                    blocksize=1048576
                    buffers-max=500
                    sync-method=next-keyframe
                    name=fd-preview-{source}
                """.format(source=self.source)

        # close bin
        self.bin += "" if Args.no_bins else "\n)\n"

    def audio_channels(self) -> int:
        return Config.getNumAudioStreams()

    def video_channels(self) -> int:
        return 1

    def is_input(self) -> bool:
        return False

    def __str__(self) -> str:
        return 'AVPreviewOutput[{}]'.format(self.source)

    def attach(self, pipeline: Gst.Pipeline):
        self.pipeline = pipeline

    def on_accepted(self, conn: socket.socket, addr: tuple[str, int]):
        self.log.debug('Adding fd %u to multifdsink', conn.fileno())

        # find fdsink and emit 'add'
        fdsink = self.pipeline.get_by_name("fd-preview-{}".format(self.source))
        if fdsink is None:
            raise Exception("could not find pipeline element for {}".format(self))
        fdsink.emit('add', conn.fileno())

        # catch disconnect
        def on_disconnect(multifdsink: Gst.Element, fileno: int):
            if fileno == conn.fileno():
                self.log.debug('fd %u removed from multifdsink', fileno)
                self.close_connection(conn)
        fdsink.connect('client-fd-removed', on_disconnect)

        # catch client-removed
        def on_client_removed(multifdsink: Gst.Element, fileno: int, status: int):
            # GST_CLIENT_STATUS_SLOW = 3,
            if fileno == conn.fileno() and status == 3:
                self.log.warning('about to remove fd %u from multifdsink '
                                 'because it is too slow!', fileno)
        fdsink.connect('client-removed', on_client_removed)
