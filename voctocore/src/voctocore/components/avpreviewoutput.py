import logging
#!/usr/bin/env python3
from vocto.video_codecs import construct_video_encoder_pipeline

from lib.tcpmulticonnection import TCPMultiConnection
from lib.config import Config
from lib.args import Args

class AVPreviewOutput(TCPMultiConnection):

    def __init__(self, source, port, use_audio_mix=False, audio_blinded=False):
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
        if source in Config.getVideoSources():
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
                               vpipeline=construct_video_encoder_pipeline('preview'),
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

    def audio_channels(self):
        return Config.getNumAudioStreams()

    def video_channels(self):
        return 1

    def is_input(self):
        return False

    def __str__(self):
        return 'AVPreviewOutput[{}]'.format(self.source)

    def attach(self, pipeline):
        self.pipeline = pipeline

    def on_accepted(self, conn, addr):
        self.log.debug('Adding fd %u to multifdsink', conn.fileno())

        # find fdsink and emit 'add'
        fdsink = self.pipeline.get_by_name("fd-preview-{}".format(self.source))
        fdsink.emit('add', conn.fileno())

        # catch disconnect
        def on_disconnect(multifdsink, fileno):
            if fileno == conn.fileno():
                self.log.debug('fd %u removed from multifdsink', fileno)
                self.close_connection(conn)
        fdsink.connect('client-fd-removed', on_disconnect)

        # catch client-removed
        def on_client_removed(multifdsink, fileno, status):
            # GST_CLIENT_STATUS_SLOW = 3,
            if fileno == conn.fileno() and status == 3:
                self.log.warning('about to remove fd %u from multifdsink '
                                 'because it is too slow!', fileno)
        fdsink.connect('client-removed', on_client_removed)
