#!/usr/bin/env python3
import logging

from gi.repository import Gst, Gdk

from lib.config import Config
from lib.tcpmulticonnection import TCPMultiConnection


class AVPreviewOutput(TCPMultiConnection):

    def __init__(self, channel, port):
        self.log = logging.getLogger('AVPreviewOutput[{}]'.format(channel))
        super().__init__(port)

        self.channel = channel

        self.bin = """
bin.(
    name=AVPreviewOutput-{channel}

    video-{channel}.
    ! {vcaps}
    ! {vpipeline}
    ! queue
        name=queue-preview-video-{channel}
    ! mux-preview-{channel}.
""".format(
            channel=self.channel,
            vcaps=Config.getVideoCaps(),
            vpipeline = self.construct_video_pipeline()
        )

        if self.channel in Config.getAudioSources():
            self.bin += """
    audio-{channel}.
    ! queue
        name=queue-preview-audio-{channel}
    ! mux-preview-{channel}.
    """.format(
            channel=self.channel)

        self.bin += """
    matroskamux
        name=mux-preview-{channel}
        streamable=true
        writing-app=Voctomix-AVPreviewOutput
    ! multifdsink
        blocksize=1048576
        buffers-max=500
        sync-method=next-keyframe
        name=fd-preview-{channel}
)
""".format(
            channel=self.channel,
            vcaps=Config.getVideoCaps(),
            vpipeline=self.construct_video_pipeline()
        )

    def audio_channels(self):
        return Config.getNumAudioStreams()

    def video_channels(self):
        return 1

    def is_input(self):
        return False

    def __str__(self):
        return 'AVPreviewOutput[{}]'.format(self.channel)

    def construct_video_pipeline(self):
        if Config.getPreviewVaapi():
            return self.construct_vaapi_video_pipeline()
        else:
            return self.construct_native_video_pipeline()

    def construct_vaapi_video_pipeline(self):
        if Gst.version() < (1, 8):
        #if False:
            vaapi_encoders = {
                'h264': 'vaapiencode_h264',
                'jpeg': 'vaapiencode_jpeg',
                'mpeg2': 'vaapiencode_mpeg2',
            }
        else:
            vaapi_encoders = {
                'h264': 'vaapih264enc',
                'jpeg': 'vaapijpegenc',
                'mpeg2': 'vaapimpeg2enc',
            }

        vaapi_encoder_options = {
            'h264': 'rate-control=cqp init-qp=10 '
                    'max-bframes=0 keyframe-period=60',
            'jpeg': 'vaapiencode_jpeg quality=90'
                    'keyframe-period=0',
            'mpeg2': 'keyframe-period=60',
        }

        size = Config.getPreviewSize()
        framerate = Config.getPreviewFramerate()
        vaapi = Config.getPreviewVaapi()

        return '''
    capsfilter
        caps=video/x-raw,interlace-mode=progressive
    ! vaapipostproc
        format=i420
        deinterlace-mode={imode}
        deinterlace-method=motion-adaptive
        width={width}
        height={height}
    ! capssetter
        caps=video/x-raw,framerate={n}/{d}
    ! {encoder} {options}
        '''.format(
            imode='interlaced' if Config.getDeinterlacePreviews() else 'disabled',
            width=size[0],
            height=size[1],
            encoder=vaapi_encoders[vaapi],
            options=vaapi_encoder_options[vaapi],
            n=framerate[0],
            d=framerate[1],
        )

    def construct_native_video_pipeline(self):
        if Config.getDeinterlacePreviews():
            pipeline = '''deinterlace mode=interlaced
    ! videorate
    ! videoscale
    ! capsfilter
        caps={target_caps}
    ! jpegenc
        quality=90'''
        else:
            pipeline = '''videorate
    ! videoscale
    ! capsfilter
        caps={target_caps}
    ! jpegenc
        quality=90'''

        return pipeline.format(
            target_caps=Config.getPreviewCaps(),
        )

    def attach(self, pipeline):
        self.pipeline = pipeline

    def on_accepted(self, conn, addr):
        self.log.debug('Adding fd %u to multifdsink', conn.fileno())
        fdsink = self.pipeline.get_by_name(
            "fd-preview-{channel}".format(
                channel=self.channel
            ))
        fdsink.emit('add', conn.fileno())

        def on_disconnect(multifdsink, fileno):
            if fileno == conn.fileno():
                self.log.debug('fd %u removed from multifdsink', fileno)
                self.close_connection(conn)

        fdsink.connect('client-fd-removed', on_disconnect)
