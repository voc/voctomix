#!/usr/bin/env python3
from lib.tcpmulticonnection import TCPMultiConnection
from lib.config import Config
from lib.args import Args
from gi.repository import Gst
import logging
import gi
gi.require_version('GstController', '1.0')


class AVPreviewOutput(TCPMultiConnection):

    def __init__(self, source, port, use_audio_mix=False, audio_blinded=False):
        # create logging interface
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
                               vpipeline=self.construct_video_pipeline(),
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

    def construct_video_pipeline(self):
        if Config.getPreviewVaapi():
            return self.construct_vaapi_video_pipeline()
        else:
            return self.construct_native_video_pipeline()

    def construct_vaapi_video_pipeline(self):
        # https://blogs.igalia.com/vjaquez/2016/04/06/gstreamer-vaapi-1-8-the-codec-split/
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
            'h264': """rate-control=cqp
                       init-qp=10
                       max-bframes=0
                       keyframe-period=60""",
            'jpeg': """quality=90
                       keyframe-period=0""",
            'mpeg2': "keyframe-period=60",
        }

        # prepare selectors
        size = Config.getPreviewResolution()
        framerate = Config.getPreviewFramerate()
        vaapi = Config.getPreviewVaapi()
        denoise = Config.getDenoiseVaapi()
        scale_method = Config.getScaleMethodVaapi()

        # generate pipeline
        # we can also force a video format here (format=I420) but this breaks scalling at least on Intel HD3000 therefore it currently removed
        return """  ! capsfilter
                        caps=video/x-raw,interlace-mode=progressive
                    ! vaapipostproc                        
                    ! video/x-raw,width={width},height={height},framerate={n}/{d},deinterlace-mode={imode},deinterlace-method=motion-adaptive,denoise={denoise},scale-method={scale_method}
                    ! {encoder}
                        {options}""".format(imode='interlaced' if Config.getDeinterlacePreviews() else 'disabled',
                                            width=size[0],
                                            height=size[1],
                                            encoder=vaapi_encoders[vaapi],
                                            options=vaapi_encoder_options[vaapi],
                                            n=framerate[0],
                                            d=framerate[1],
                                            denoise=denoise,
                                            scale_method=scale_method,
                                            )

    def construct_native_video_pipeline(self):
        # maybe add deinterlacer
        if Config.getDeinterlacePreviews():
            pipeline = """  ! deinterlace
                                mode=interlaced
                            """
        else:
            pipeline = ""

        # build rest of the pipeline
        pipeline += """ ! videorate
                        ! videoscale
                        ! {vcaps}
                        ! jpegenc
                            quality = 90""".format(vcaps=Config.getPreviewCaps())
        return pipeline

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
