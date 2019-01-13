#!/usr/bin/env python3
import logging

from lib.config import Config
from lib.tcpmulticonnection import TCPMultiConnection


class AVPreviewOutput(TCPMultiConnection):

    def __init__(self, channel, port):
        self.log = logging.getLogger('AVPreviewOutput[{}]'.format(channel))
        super().__init__(port)

        self.channel = channel

        if Config.has_option('previews', 'videocaps'):
            target_caps = Config.get('previews', 'videocaps')
        else:
            target_caps = Config.get('mix', 'videocaps')

        self.pipe = """
video-{channel}.
! {vpipeline}
! queue
    name=queue-preview-video-{channel}
! mux-preview-{channel}.
        """.format(
            channel=self.channel,
            vpipeline=self.construct_video_pipeline(target_caps)
        )

        for audiostream in range(0, Config.getint('mix', 'audiostreams')):
            self.pipe += """
audio-{channel}-{audiostream}.
! queue
    name=queue-preview-audio-{channel}-{audiostream}
! mux-preview-{channel}.
            """.format(
                channel=self.channel,
                audiostream=audiostream
            )

        self.pipe += """
matroskamux
    name=mux-preview-{channel}
    streamable=true
    writing-app=Voctomix-AVPreviewOutput
! multifdsink
    blocksize=1048576
    buffers-max=500
    sync-method=next-keyframe
    name=fd-preview-{channel}
        """.format(
            channel=self.channel
        )

    def __str__(self):
        return 'AVPreviewOutput[{}]'.format(self.channel)

    def construct_video_pipeline(self, target_caps):
        vaapi_enabled = Config.has_option('previews', 'vaapi')
        if vaapi_enabled:
            return self.construct_vaapi_video_pipeline(target_caps)

        else:
            return self.construct_native_video_pipeline(target_caps)

    def construct_vaapi_video_pipeline(self, target_caps):
        if Gst.version() < (1, 8):
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

        encoder = Config.get('previews', 'vaapi')
        do_deinterlace = Config.getboolean('previews', 'deinterlace')

        caps = Gst.Caps.from_string(target_caps)
        struct = caps.get_structure(0)
        _, width = struct.get_int('width')
        _, height = struct.get_int('height')
        (_, framerate_numerator,
         framerate_denominator) = struct.get_fraction('framerate')

        return '''
capsfilter caps=video/x-raw,interlace-mode=progressive
! vaapipostproc
    format=i420
    deinterlace-mode={imode}
    deinterlace-method=motion-adaptive
    width={width}
    height={height}
! capssetter caps=video/x-raw,framerate={n}/{d}
! {encoder} {options}
        '''.format(
            imode='interlaced' if do_deinterlace else 'disabled',
            width=width,
            height=height,
            encoder=vaapi_encoders[encoder],
            options=vaapi_encoder_options[encoder],
            n=framerate_numerator,
            d=framerate_denominator,
        )

    def construct_native_video_pipeline(self, target_caps):
        do_deinterlace = Config.getboolean('previews', 'deinterlace')

        if do_deinterlace:
            pipeline = '''deinterlace mode={imode}
! videorate
! videoscale
! {target_caps}
! jpegenc quality=90'''
        else:
            pipeline = '''videoscale
! {target_caps}
! jpegenc quality=90'''

        return pipeline.format(
            imode='interlaced' if do_deinterlace else 'disabled',
            target_caps=target_caps,
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
