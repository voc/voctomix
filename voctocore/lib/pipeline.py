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
from vocto.port import Port

# input ports
PORT_SOURCES_IN = 10000
PORT_SOURCE_BACKGROUND = 16000
PORT_SOURCES_BLANK = 17000
PORT_AUDIO_SOURCE_BLANK = 18000
# output ports
PORT_MIX_OUT = 11000
PORT_MIX_PREVIEW = 12000
PORT_SOURCES_OUT = 13000
PORT_SOURCES_PREVIEW = 14000
PORT_LIVE_OUT = 15000
PORT_SLIDES_LIVE_OUT = 15001


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
        self.ports = []

        # create A/V sources
        self.log.info('Creating %u AVSources: %s', len(names), names)
        for idx, name in enumerate(names):
            # count port and create source
            source = spawn_source(name, PORT_SOURCES_IN + idx)
            self.bins.append(source)
            self.ports.append(Port(name, source))

            if Config.getboolean('mirrors', 'enabled'):
                dest=AVRawOutput(name, PORT_SOURCES_OUT + idx)
                self.bins.append(dest)
                self.ports.append(Port(name, dest))

            # check for source preview selection
            if Config.getboolean('previews', 'enabled'):
                # count preview port and create source
                dest=AVPreviewOutput(name, PORT_SOURCES_PREVIEW + idx)
                self.bins.append(dest)
                self.ports.append(Port("preview-%s" % name, dest))

        # create audio mixer
        self.log.info('Creating Audiomixer')
        self.amix=AudioMix()
        self.bins.append(self.amix)

        # create video mixer
        self.log.info('Creating Videomixer')
        self.vmix=VideoMix()
        self.bins.append(self.vmix)

        # create background source
        source=spawn_source(
            'background', PORT_SOURCE_BACKGROUND, has_audio=False)
        self.bins.append(source)
        self.ports.append(Port('background', source))

        # create mix TCP output
        dest=AVRawOutput('mix', PORT_MIX_OUT)
        self.bins.append(dest)
        self.ports.append(Port('mix', dest))

        # create mix preview TCP output
        if Config.getboolean('previews', 'enabled'):
            dest=AVPreviewOutput('mix', PORT_MIX_PREVIEW)
            self.bins.append(dest)
            self.ports.append(Port('preview-mix', dest))

        # create stream blanker sources and mixer
        if Config.getboolean('stream-blanker', 'enabled'):
            names=Config.getlist('stream-blanker', 'sources')
            if len(names) < 1:
                raise RuntimeError('At least one StreamBlanker-Source must '
                                   'be configured or the '
                                   'StreamBlanker disabled!')
            for idx, name in enumerate(names):
                source=spawn_source('sb-{}'.format(name),
                                      PORT_SOURCES_BLANK + idx,
                                      has_audio=False)
                self.bins.append(source)
                self.ports.append(Port('sb-{}'.format(name), source))

            source=spawn_source('sb',
                                  PORT_AUDIO_SOURCE_BLANK,
                                  has_video=False,
                                  force_num_streams=1)
            self.bins.append(source)
            self.ports.append(Port('sb-audio', source))

            self.log.info('Creating Stream Blanker Mixer')
            self.streamblanker=StreamBlanker()
            self.bins.append(self.streamblanker)
            dest=AVRawOutput('mix-sb', PORT_LIVE_OUT)
            self.bins.append(dest)
            self.ports.append(Port('live-mix', dest))
            if Config.has_option('mix', 'slides_source_name'):
                dest=AVRawOutput('mix-sb-slides', PORT_SLIDES_LIVE_OUT)
                self.bins.append(dest)
                self.ports.append(Port('live-slides', dest))

        for bin in self.bins:
            self.log.info("%s\n%s", bin, bin.bin)

        # concatinate pipeline string
        pipeline="\n\n".join(bin.bin for bin in self.bins)

        # launch gstreamer pipeline
        self.pipeline=Gst.parse_launch(pipeline)

        # attach pads
        for bin in self.bins:
            bin.attach(self.pipeline)

        self.pipeline.use_clock(Clock)

        # fetch all queues
        self.queues=[]

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

        self.draw_pipeline=Args.dot

        self.pipeline.set_state(Gst.State.PLAYING)

    def on_eos(self, bus, message):
        self.log.debug('Received End-of-Stream-Signal on Source-Pipeline')

    def on_error(self, bus, message):
        self.log.error('Received Error-Signal on Source-Pipeline')
        (error, debug)=message.parse_error()
        self.log.debug('Error-Details: #%u: %s', error.code, debug)

    def on_state_changed(self, bus, message):
        if message.parse_state_changed().newstate == Gst.State.PLAYING:
            # make DOT file from pipeline
            self.log.debug('Generating DOT image of avsource pipeline')
            Gst.debug_bin_to_dot_file(self.pipeline, 0, "pipeline")
            self.draw_pipeline=False
        elif self.draw_pipeline and message.parse_state_changed().newstate == Gst.State.PAUSED:
            self.draw_pipeline=True
