#!/usr/bin/env python3
import gi
import logging
import sys

from lib.config import Config
from gi.repository import Gst

gi.require_version('GstController', '1.0')

log = logging.getLogger('audio_codecs')

def get_spread_matrix(available_channels):
    ''' spread number of output audio channels to one on the given list by using an audiomixmatrix'''
    # create identity matrix for all channels
    in_channels = Config.getAudioChannels()
    out_channels = None
    for channels in available_channels:
        if channels >= in_channels:
            out_channels = channels
            break
    if out_channels == in_channels:
        return ""
    if out_channels is None:
        log.error("audio encoder can't handle {} channels".format(in_channels))
        sys.exit(-1)
    matrix = [[0.0 for x in range(0, in_channels)]
              for x in range(0, out_channels)]
    for i in range(0, min(in_channels,out_channels)):
        matrix[i][i] = 1.0
    return """! audiomixmatrix
                in_channels={in_channels}
                out_channels={out_channels}
                matrix="{matrix}"
                """.format(in_channels=in_channels,
                            out_channels=out_channels,
                            matrix=str(matrix).replace("[","<").replace("]",">")
                            )

def construct_audio_encoder_pipeline(section):
    encoder = Config.getAudioEncoder(section)
    codec, options = Config.getAudioCodec(section)
    acaps = Config.getAudioCaps(section)

    pipeline = ""

    if encoder == 'cpu':
        # build rest of the pipeline
        pipeline += """! audioconvert
                       {spread} ! {encoder}""".format(spread=get_spread_matrix([1,6]),
                                                      encoder="avenc_aac"
                                                      )
    else:
        log.error("Unknown audio encoder {}".format(encoder))
        sys.exit(-1)

    if options:
        pipeline += """
                        {options}""".format(options='\n'.join(options))

    return pipeline
