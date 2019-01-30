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

# input ports
PORT_SOURCES_IN = 10000
PORT_SOURCE_BACKGROUND = 16000
# output ports
PORT_SOURCES_PREVIEW = 14000
PORT_MIX_OUT = 11000
PORT_MIX_PREVIEW = 12000

class Pipeline(object):
    """mixing, streaming and encoding pipeline constuction and control"""

    def __init__(self):
        self.log = logging.getLogger('Pipeline')
        # log capabilities
        self.log.info('Video-Caps configured to: %s',
                      Config.get('mix', 'videocaps'))
        self.log.info('Audio-Caps configured to: %s',
                      Config.get('mix', 'audiocaps'))

        # get A/B sources from config
        names = Config.getlist('mix', 'sources')
        if len(names) < 1:
            raise RuntimeError("At least one AVSource must be configured!")

        # collect bins for all modules
        self.bins = []

        # create A/V sources
        self.log.info('Creating %u AVSources: %s', len(names), names)
        for idx, name in enumerate(names):
            # count port and create source
            port = PORT_SOURCES_IN + idx
            source = spawn_source(name, port)
            self.log.info('Creating AVSource %s as %s', name, source)
            self.bins.append(source)

            # check for source preview selection
            if Config.getboolean('previews', 'enabled'):
                # count preview port and create source
                port = PORT_SOURCES_PREVIEW + idx
                preview = AVPreviewOutput(name, port)
                self.log.info('Creating Preview-Output for AVSource %s '
                              'at tcp-port %u', name, port)
                self.bins.append(preview)

        # create audio mixer
        self.log.info('Creating Audiomixer')
        self.amix = AudioMix()
        self.bins.append(self.amix)

        # create video mixer
        self.log.info('Creating Videomixer')
        self.vmix = VideoMix()
        self.bins.append(self.vmix)

        # create background source
        port = PORT_SOURCE_BACKGROUND
        self.log.info('Creating Mixer-Background VSource at %u', port)
        self.bins.append(spawn_source('background', port, has_audio=False))

        # create mix TCP output
        port = PORT_MIX_OUT
        self.log.info('Creating Mixer-Output at tcp-port %u', port)
        self.bins.append(AVRawOutput('mix', port))

        # create mix preview TCP output
        if Config.getboolean('previews', 'enabled'):
            port = PORT_MIX_PREVIEW
            self.log.info('Creating Preview-Output for Mix'
                          'at tcp-port %u', port)
            self.bins.append(AVPreviewOutput('mix', port))

        # create stream blanker sources and mixer
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
                self.bins.append(spawn_source('sb-{}'.format(name),
                                               port,
                                               has_audio=False))

            port = 18000
            self.log.info('Creating StreamBlanker ASource at tcp-port %u',
                          port)
            self.bins.append(spawn_source('sb',
                                           port,
                                           has_video=False,
                                           force_num_streams=1))

            self.log.info('Creating Stream Blanker Mixer')
            self.streamblanker = StreamBlanker()
            self.bins.append(self.streamblanker)
            port = 15000
            self.log.info('Creating Stream Blanker Output at tcp-port %u', port)
            self.bins.append(AVRawOutput('mix-sb', port))
            if Config.has_option('mix', 'slides_source_name'):
                port = 15001
                self.log.info(
                    'Creating Slides Stream Blanker Output at tcp-port %u', port)
                self.bins.append(AVRawOutput(
                    'mix-sb-slides', port))

        for bin in self.bins:
            self.log.info("%s\n%s", bin, bin.bin)

        # concatinate pipeline string
        pipeline = "\n\n".join(bin.bin for bin in self.bins)

        # launch gstreamer pipeline
        self.pipeline = Gst.parse_launch(pipeline)

        # attach pads
        for bin in self.bins:
            bin.attach(self.pipeline)

        self.pipeline.use_clock(Clock)

        # fetch all queues
        self.queues = []

        def query_queues(element):
            if element.find_property("current-level-time"):
                self.queues.append(element)

        self.pipeline.iterate_recurse().foreach(query_queues)

        self.log.debug('Binding End-of-Stream-Signal on Source-Pipeline')
        self.pipeline.bus.add_signal_watch()
        self.pipeline.bus.connect("message::eos", self.on_eos)
        self.pipeline.bus.connect("message::error", self.on_error)
        self.pipeline.bus.connect(
            "message::state-changed", self.on_state_changed)

        self.draw_pipeline = Args.dot

        self.pipeline.set_state(Gst.State.PLAYING)

    def on_eos(self, bus, message):
        self.log.debug('Received End-of-Stream-Signal on Source-Pipeline')

    def on_error(self, bus, message):
        self.log.error('Received Error-Signal on Source-Pipeline')
        (error, debug) = message.parse_error()
        self.log.debug('Error-Details: #%u: %s', error.code, debug)

    def on_state_changed(self, bus, message):
        if message.parse_state_changed().newstate == Gst.State.PLAYING:
            # make DOT file from pipeline
            self.log.debug('Generating DOT image of avsource pipeline')
            Gst.debug_bin_to_dot_file(self.pipeline, 0, "pipeline")
            self.draw_pipeline = False
        elif self.draw_pipeline and message.parse_state_changed().newstate == Gst.State.PAUSED:
            self.draw_pipeline = True
