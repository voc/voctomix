#!/usr/bin/env python3
import logging

from gi.repository import Gst

# import library components
from lib.config import Config
from lib.sources import spawn_source
from lib.avrawoutput import AVRawOutput
from lib.avpreviewoutput import AVPreviewOutput
from lib.videomix import VideoMix
from lib.audiomix import AudioMix
from lib.streamblanker import StreamBlanker
from lib.args import Args
from lib.clock import Clock


class Pipeline(object):
    """mixing, streaming and encoding pipeline constuction and control"""

    def __init__(self):
        self.log = logging.getLogger('Pipeline')
        self.log.info('Video-Caps configured to: %s',
                      Config.get('mix', 'videocaps'))
        self.log.info('Audio-Caps configured to: %s',
                      Config.get('mix', 'audiocaps'))

        names = Config.getlist('mix', 'sources')
        if len(names) < 1:
            raise RuntimeError("At least one AVSource must be configured!")

        self.pipes = []

        self.log.info('Creating %u AVSources: %s', len(names), names)
        for idx, name in enumerate(names):
            port = 10000 + idx

            source = spawn_source(name, port)
            self.log.info('Creating AVSource %s as %s', name, source)
            self.pipes.append(source)

            if Config.getboolean('previews', 'enabled'):
                port = 14000 + idx
                self.log.info('Creating Preview-Output for AVSource %s '
                              'at tcp-port %u', name, port)

                preview = AVPreviewOutput(name, port)
                self.pipes.append(preview)

        self.log.info('Creating Audiomixer')
        self.amix = AudioMix()
        self.pipes.append(self.amix)

        self.log.info('Creating Videomixer')
        self.vmix = VideoMix()
        self.pipes.append(self.vmix)

        port = 16000
        self.log.info('Creating Mixer-Background VSource at %u', port)
        self.pipes.append(spawn_source('background', port, has_audio=False))

        port = 11000
        self.log.info('Creating Mixer-Output at tcp-port %u', port)
        self.pipes.append(AVRawOutput('mix', port))

        if Config.getboolean('previews', 'enabled'):
            port = 12000
            self.log.info('Creating Preview-Output for Mix'
                          'at tcp-port %u', port)

            self.pipes.append(AVPreviewOutput('mix', port))

        if Config.getboolean('stream-blanker', 'enabled'):
            names = Config.getlist('stream-blanker', 'sources')
            if len(names) < 1:
                raise RuntimeError('At least one StreamBlanker-Source must '
                                   'be configured or the '
                                   'StreamBlanker disabled!')
            for idx, name in enumerate(names):
                port = 17000 + idx

                self.log.info('Creating StreamBlanker VSource %s at %u',
                              name, port)
                self.pipes.append(spawn_source('video-sb-{}'.format(name),
                                               port,
                                               has_audio=False))

            port = 18000
            self.log.info('Creating StreamBlanker ASource at tcp-port %u',
                          port)
            self.pipes.append(spawn_source('audio-sb',
                                           port,
                                           has_video=False,
                                           force_num_streams=1))

            self.log.info('Creating StreamBlanker')
            self.pipes.append(StreamBlanker())
            port = 15000
            self.log.info('Creating StreamBlanker-Output at tcp-port %u', port)
            self.pipes.append(AVRawOutput('sb', port))
            if Config.has_option('mix', 'slides_source_name'):
                port = 15001
                self.log.info(
                    'Creating SlideStreamBlanker-Output at tcp-port %u', port)
                self.pipes.append(AVRawOutput(
                    'sb-slides', port))

        # concatinate pipeline string
        pipeline = "\n\n".join(pipe.pipe for pipe in self.pipes)
        self.log.info(pipeline)

        # launch gstreamer pipeline
        self.pipeline = Gst.parse_launch(pipeline)

        # make DOT file from pipeline
        if Args.dot:
            self.log.debug('Generating DOT image of avsource pipeline')
            Gst.debug_bin_to_dot_file(self.pipeline, 0, "pipeline")

        # attach pads
        for pipe in self.pipes:
            pipe.attach(self.pipeline)

        self.pipeline.use_clock(Clock)

        self.log.debug('Binding End-of-Stream-Signal on Source-Pipeline')
        self.pipeline.bus.add_signal_watch()
        self.pipeline.bus.connect("message::eos", self.on_eos)
        self.pipeline.bus.connect("message::error", self.on_error)

        self.pipeline.set_state(Gst.State.PLAYING)

    def on_eos(self, bus, message):
        self.log.debug('Received End-of-Stream-Signal on Source-Pipeline')

    def on_error(self, bus, message):
        self.log.error('Received Error-Signal on Source-Pipeline')
        (error, debug) = message.parse_error()
        self.log.debug('Error-Details: #%u: %s', error.code, debug)
