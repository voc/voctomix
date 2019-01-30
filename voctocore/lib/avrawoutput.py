#!/usr/bin/env python3
import logging

from lib.config import Config
from lib.tcpmulticonnection import TCPMultiConnection


class AVRawOutput(TCPMultiConnection):

    def __init__(self, channel, port, has_audio=True):
        self.log = logging.getLogger('AVRawOutput[{}]'.format(channel))
        super().__init__(port)

        self.channel = channel

        self.bin = """
bin.(
    name=AVRawOutput-{channel}

    video-{channel}.
    ! queue
        name=queue-mux-video-{channel}
    ! mux-{channel}.
        """.format(
            channel=self.channel
        )

        if has_audio:
            for audiostream in range(0, Config.getint('mix', 'audiostreams')):
                self.bin += """
    audio-{channel}-{audiostream}.
    ! queue
        name=queue-mux-audio-{channel}-{audiostream}
    ! mux-{channel}.
                """.format(
                        channel=self.channel,
                        audiostream=audiostream,
                    )

        self.bin += """
    matroskamux
        name=mux-{channel}
        streamable=true
        writing-app=Voctomix-AVRawOutput
    ! multifdsink
        blocksize=1048576
        buffers-max={buffers_max}
        sync-method=next-keyframe
        name=fd-{channel}
        """.format(
            buffers_max=Config.getint(
                'output-buffers', self.channel, fallback=500),
            channel=self.channel
        )
        self.bin += "\n)"

    def __str__(self):
        return 'AVRawOutput[{}]'.format(self.channel)

    def attach(self, pipeline):
        self.pipeline = pipeline

    def on_accepted(self, conn, addr):
        self.log.debug('Adding fd %u to multifdsink', conn.fileno())
        fdsink = self.pipeline.get_by_name(
            "fd-{channel}".format(
                channel=self.channel
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
