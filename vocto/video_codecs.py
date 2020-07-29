#!/usr/bin/env python3
import logging
import gi
import sys

from lib.config import Config
from gi.repository import Gst

gi.require_version('GstController', '1.0')

log = logging.getLogger('video_codecs')

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

v4l2_encoders = {
        'h264': 'v4l2h264enc',
        'jpeg': 'v4l2jpegenc',
}

cpu_encoders = {
    'jpeg': "jpegenc"
    # TODO: add h264 and mpeg2 ?
}

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

cpu_decoders = {
    'h264': """ video/x-h264
                ! avdec_h264""",
    'jpeg': """ image/jpeg
                ! jpegdec""",
    'mpeg2': """video/mpeg
                    mpegversion=2
                ! mpeg2dec"""
}

def construct_video_encoder_pipeline(section):
    encoder = Config.getVideoEncoder(section)
    codec, options = Config.getVideoCodec(section)
    vcaps = Config.getVideoCaps(section)

    pipeline = ""

    if encoder == 'vaapi':
        if codec not in vaapi_encoders:
            log.error("Unkown codec '{}' for video encoder '{}'. Falling back to 'h264'.".format(codec,encoder))
            sys.exit(-1)
        # generate pipeline
        # we can also force a video format here (format=I420) but this breaks scalling at least on Intel HD3000 therefore it currently removed
        pipeline = """  ! capsfilter
                            caps=video/x-raw,interlace-mode=progressive
                        ! vaapipostproc
                        ! {encoder}
                        ! {vcaps} """.format(vcaps=vcaps,
                                              encoder=vaapi_encoders[codec]
                                             )
    elif encoder == 'v4l2':
        if codec not in v4l2_encoders:
            log.error("Unkown codec '{}' for video encoder '{}'. Falling back to 'h264'.".format(codec,encoder))
            sys.exit(-1)
        pipeline = """  ! capsfilter
                            caps=video/x-raw,interlace-mode=progressive
                        ! {encoder}
                        ! {vcaps}""".format(vcaps=vcaps,
                                              encoder=v4l2_encoders[codec]
                                             )
    elif encoder == "cpu":
        if codec not in cpu_encoders:
            log.error("Unkown codec '{}' for video encoder '{}'.".format(codec,encoder))
            sys.exit(-1)
        # maybe add deinterlacer
        if Config.getDeinterlace(section):
            pipeline += """ ! deinterlace
                                mode=interlaced
                        """
        # build rest of the pipeline
        pipeline += """ ! videorate
                        ! videoscale
                        ! {encoder}
                        ! {vcaps}""".format(vcaps=vcaps,
                                            encoder=cpu_encoders[codec],
                                           )
    else:
        log.error("Unkown video decoder '{}'.".format(encoder))
        sys.exit(-1)

    if options:
        pipeline += """
                        {options}""".format(options='\n'.join(options))

    return pipeline


def construct_video_decoder_pipeline(section):
    decoder = Config.getVideoDecoder(section)
    codec, options = Config.getVideoCodec(section)
    if decoder == 'vaapi':
        return vaapi_decoders[codec]
    elif decoder == 'cpu':
        return cpu_decoders[codec]
    else:
        log.error("Unkown video decoder '{}'.".format(encoder))
        exit(-1)
