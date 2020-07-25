#!/usr/bin/env python3
import gi

from lib.config import Config
from gi.repository import Gst

gi.require_version('GstController', '1.0')


def construct_video_encoder_pipeline(section):
    if Config.getVaapi(section):
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
        size = Config.getVResolution(section)
        framerate = Config.getVFramerate(section)
        vaapi = Config.getVaapi(section)
        denoise = Config.getVaapiDenoise(section)
        scale_method = Config.getVaapiScaleMethod(section)

        # generate pipeline
        # we can also force a video format here (format=I420) but this breaks scalling at least on Intel HD3000 therefore it currently removed
        return """  ! capsfilter
                        caps=video/x-raw,interlace-mode=progressive
                    ! vaapipostproc
                    ! video/x-raw,width={width},height={height},framerate={n}/{d},deinterlace-mode={imode},deinterlace-method=motion-adaptive,denoise={denoise},scale-method={scale_method}
                    ! {encoder}
                        {options}""".format(imode='interlaced' if Config.getVDeinterlace(section) else 'disabled',
                                            width=size[0],
                                            height=size[1],
                                            encoder=vaapi_encoders[vaapi],
                                            options=vaapi_encoder_options[vaapi],
                                            n=framerate[0],
                                            d=framerate[1],
                                            denoise=denoise,
                                            scale_method=scale_method,
                                            )
    else:
        pipeline = ""

        # maybe add deinterlacer
        if Config.getVDeinterlace(section):
            pipeline += """ ! deinterlace
                                mode=interlaced
                        """

        # build rest of the pipeline
        pipeline += """ ! videorate
                        ! videoscale
                        ! {vcaps}
                        ! jpegenc
                            quality = 90""".format(vcaps=Config.getVCaps('section'))
        return pipeline


def construct_video_decoder_pipeline(section):
    if Config.getVaapi(section):
        if Gst.version() < (1, 8):
            vaapi_decoders = {
                'h264': 'vaapidecode_h264',
                'mpeg2': 'vaapidecode_mpeg2',
            }
        else:
            vaapi_decoders = {
                'h264': 'vaapih264dec',
                'mpeg2': 'vaapimpeg2dec',
            }

        return vaapi_decoders[Config.getVaapi(section)]
    else:
        return """image/jpeg
                  ! jpegdec"""
