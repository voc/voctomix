#!/usr/bin/env python3
import logging
import gi
gi.require_version('GstController', '1.0')
from gi.repository import Gst

from lib.config import Config
from lib.tcpmulticonnection import TCPMultiConnection


class AVPreviewOutput(TCPMultiConnection):

    def __init__(self, source, port, use_audio_mix=False):
        self.log = logging.getLogger('AVPreviewOutput[{}]'.format(source))
        super().__init__(port)

        self.source = source

        self.bin = """
            bin.(
                name=AVPreviewOutput-{source}

                video-{source}.
                ! {vcaps}
                ! {vpipeline}
                ! queue
                    name=queue-preview-video-{source}
                ! mux-preview-{source}.

                {use_audio}audio-{source}.
                ! queue
                    name=queue-preview-audio-{source}
                ! mux-preview-{source}.

                matroskamux
                    name=mux-preview-{source}
                    streamable=true
                    writing-app=Voctomix-AVPreviewOutput
                ! multifdsink
                    blocksize=1048576
                    buffers-max=500
                    sync-method=next-keyframe
                    name=fd-preview-{source}
            )
            """.format(source=self.source,
                       use_audio="" if use_audio_mix else "source-",
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
        return 'AVPreviewOutput[{}]'.format(self.source)

    def construct_video_pipeline(self):
        if Config.getPreviewVaapi():
            return self.construct_vaapi_video_pipeline()
        else:
            return self.construct_native_video_pipeline()

    def construct_vaapi_video_pipeline(self):
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

        size = Config.getPreviewResolution()
        framerate = Config.getPreviewFramerate()
        vaapi = Config.getPreviewVaapi()

        return '''capsfilter
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
            '''.format(imode='interlaced' if Config.getDeinterlacePreviews() else 'disabled',
                       width=size[0],
                       height=size[1],
                       encoder=vaapi_encoders[vaapi],
                       options=vaapi_encoder_options[vaapi],
                       n=framerate[0],
                       d=framerate[1],
                       )

    def construct_native_video_pipeline(self):
        pipeline = """deinterlace mode={imode}
            ! videorate
            ! videoscale
            ! capsfilter
                caps={target_caps}
            ! jpegenc
                quality=90""".format(target_caps=Config.getPreviewCaps(),
                       imode='interlaced' if Config.getDeinterlacePreviews() else 'disabled')

        return pipeline

    def attach(self, pipeline):
        self.pipeline = pipeline

    def on_accepted(self, conn, addr):
        self.log.debug('Adding fd %u to multifdsink', conn.fileno())
        fdsink = self.pipeline.get_by_name(
            "fd-preview-{source}".format(
                source=self.source
            ))
        fdsink.emit('add', conn.fileno())

        def on_disconnect(multifdsink, fileno):
            if fileno == conn.fileno():
                self.log.debug('fd %u removed from multifdsink', fileno)
                self.close_connection(conn)

        fdsink.connect('client-fd-removed', on_disconnect)
