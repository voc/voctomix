#!/usr/bin/env python3
from lib.tcpmulticonnection import TCPMultiConnection
from lib.config import Config
from lib.args import Args
from gi.repository import Gst
import logging
import gi
gi.require_version('GstController', '1.0')


class AVPreviewOutput(TCPMultiConnection):

    def __init__(self, source, port, use_audio_mix=False):
        self.log = logging.getLogger('AVPreviewOutput[{}]'.format(source))
        super().__init__(port)

        self.source = source
        self.audio_streams = Config.getAudioStreams().get_stream_source()
        self.audio_streams.append('mix')
        self.audio_streams.append('mix-blinded')
        self.audio_streams.append('cam3')

        self.bin = "" if Args.no_bins else """
            bin.(
                name=AVPreviewOutput-{source}
                """.format(source=self.source)

        self.bin += """
                video-{source}.
                ! {vcaps}
                ! queue
                    max-size-time=3000000000
                    name=queue-preview-video-{source}
                ! {vpipeline}
                ! queue
                    max-size-time=3000000000
                    name=queue-mux-preview-{source}
                ! mux-preview-{source}.
                """.format(source=self.source,
                           vpipeline=self.construct_video_pipeline(),
                           vcaps=Config.getVideoCaps()
                           )

        if source in self.audio_streams:
            self.bin +=                """
                    {use_audio}audio-{source}.
                    ! queue
                        max-size-time=3000000000
                        name=queue-preview-audio-{source}
                    ! mux-preview-{source}.
                    """.format(source=self.source,
                           use_audio="" if use_audio_mix else "source-",
                           vpipeline=self.construct_video_pipeline(),
                           )

        self.bin +=                """
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
                """.format(source=self.source
                           )
        self.bin += "" if Args.no_bins else  """
        )
        """

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
        deinterlace = imode = "deinterlace mode=interlaced" if Config.getDeinterlacePreviews() else ""
        pipeline = """{deinterlace}videorate
            ! videoscale
            ! {target_caps}
            ! jpegenc
                quality=90""".format(target_caps=Config.getPreviewCaps(),
                                     deinterlace=deinterlace
                                     )

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
