#!/usr/bin/env python3
import gi
import logging
import sys

from lib.config import Config
from gi.repository import Gst

gi.require_version('GstController', '1.0')
log = logging.getLogger('audio_codecs')

# list of supported audio codecs as named by gst
encoders = {'fdkaacenc',
            'avenc_aac',
            'avdec_mp3',
            'flacenc',
            'wavenc',
            'opus',
            'avenc_mp3',
            'lame'
            'avenc_s302m'}


def create_mixmatrix(in_channels: int, out_channels: int, channel_mapping: str):
    """ create a audiomixmatrix pipeline block from a givin channel mapping
    :param in_channels: number of input channels
    :param out_channels: number of output channels
    :param channel_mapping: mapping for output channel map
    :return: audiomixmatrix pipeline block
    """

    # create matrix filled with 0.0 (all channels muted)
    matrix = [[0.0 for x in range(0, in_channels)]
              for x in range(0, out_channels)]

    # apply channel map to matrix
    mappings = channel_mapping.split(';')
    for mapping in mappings:
        in_channel, out_channel = mapping.split(',')
        matrix[int(in_channel)][int(out_channel)] = 1.0

    pipeline = """! audiomixmatrix
               in_channels={in_channels}
               out_channels={out_channels}
               matrix="{matrix}"
               """.format(in_channels=in_channels,
                          out_channels=out_channels,
                          matrix=str(matrix).replace("[", "<").replace("]", ">")
                          )
    return pipeline


def construct_audio_encoder_pipeline(section):
    """
    Build audio encoder pipeline block including an adapter matrix for channel mapping
    :param section: Name of the config section this block is for
    :return: String containing the pipeline block
    """
    encoder = Config.get_audio_encoder(section)
    encoder_options = None
    # check if we have an option string as part of the codec config
    if ',' in encoder:
        encoder, encoder_options = encoder.split(',', 1)

    pipeline = ""
    if encoder in encoders:
        pipeline += """! audioconvert
                           {mixmatrix} ! {encoder} ! {acaps}
                    """.format(mixmatrix=create_mixmatrix(Config.getAudioChannels(),
                                                          Config.get_sink_audio_channels(section),
                                                          Config.get_sink_audio_map(section)),
                               encoder=encoder,
                               acaps=Config.getAudioCaps(section))
    else:
        log.error("Unknown audio encoder {}".format(encoder))
        sys.exit(-1)

    if encoder_options:
        pipeline += """{options}""".format(options=encoder_options)

    return pipeline
