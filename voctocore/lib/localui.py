#!/usr/bin/env python3
import logging

from lib.args import Args
from lib.config import Config
from lib.tcpmulticonnection import TCPMultiConnection

class LocalUi():

    def __init__(self, source, port, use_audio_mix=False, audio_blinded=False):
        # create logging interface
        self.log = logging.getLogger('LocalUI'.format(source))

        # initialize super
        #super().__init__(port)

        # remember things
        self.source = source

        # open bin
        #self.bin = "" if Args.no_bins else """
        #    bin.(
        #        name=LocalUI
        #        """

        self.bin = ""
        # video pipeline
        self.bin += """
                video-mix.
                ! {vcaps}
                ! queue
                    max-size-time=3000000000
                    name=queue-mux-video-localui
                ! autovideosink
                """.format(source=self.source,
                          vcaps=Config.getVideoCaps())

        # close bin
        #self.bin += "" if Args.no_bins else "\n)\n"

    def port(self):
        return 0

    def num_connections(self):
        return 0

    def audio_channels(self):
        return Config.getNumAudioStreams()

    def video_channels(self):
        return 1

    def is_input(self):
        return False

    def __str__(self):
        return 'LocalUI[{}]'.format(self.source)

    def attach(self, pipeline):
        self.pipeline = pipeline
