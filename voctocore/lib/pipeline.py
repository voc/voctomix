#!/usr/bin/env python3
import logging
import re
import sys

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
from vocto.debug import gst_generate_dot

class Pipeline(object):
    """mixing, streaming and encoding pipeline constuction and control"""

    def __init__(self):
        self.log = logging.getLogger('Pipeline')
        # log capabilities
        self.log.info('Video-Caps configured to: %s', Config.getVideoCaps())
        self.log.info('Audio-Caps configured to: %s', Config.getAudioCaps())

        # get A/B sources from config
        sources = Config.getSources()
        if len(sources) < 1:
            raise RuntimeError("At least one AVSource must be configured!")

        # collect bins for all modules
        self.bins = []
        self.ports = []

        # create A/V sources
        self.log.info('Creating %u AVSources: %s', len(sources), sources)
        for idx, source_name in enumerate(sources):
            # count port and create source
            source = spawn_source(source_name, Port.SOURCES_IN + idx)
            self.bins.append(source)
            self.ports.append(Port(source_name, source))

            if Config.getMirrorsEnabled():
                if source_name in Config.getMirrorsSources():
                    dest = AVRawOutput(source_name, Port.SOURCES_OUT + idx)
                    self.bins.append(dest)
                    self.ports.append(Port(source_name, dest))

            # check for source preview selection
            if Config.getPreviewsEnabled():
                # count preview port and create source
                dest = AVPreviewOutput(source_name, Port.SOURCES_PREVIEW + idx)
                self.bins.append(dest)
                self.ports.append(Port("preview-%s" % source_name, dest))

        # create audio mixer
        self.log.info('Creating Audiomixer')
        self.amix = AudioMix()
        self.bins.append(self.amix)

        # create video mixer
        self.log.info('Creating Videomixer')
        self.vmix = VideoMix()
        self.bins.append(self.vmix)

        # create background source
        source = spawn_source(
            'background', Port.SOURCE_BACKGROUND, has_audio=False)
        self.bins.append(source)
        self.ports.append(Port('background', source))

        # create mix TCP output
        dest = AVRawOutput('mix', Port.MIX_OUT)
        self.bins.append(dest)
        self.ports.append(Port('mix', dest))

        # create mix preview TCP output
        if Config.getPreviewsEnabled():
            dest = AVPreviewOutput('mix', Port.MIX_PREVIEW)
            self.bins.append(dest)
            self.ports.append(Port('preview-mix', dest))

        # create stream blanker sources and mixer
        if Config.getStreamBlankerEnabled():
            sources = Config.getStreamBlankerSources()
            if len(sources) < 1:
                raise RuntimeError('At least one StreamBlanker-Source must '
                                   'be configured or the '
                                   'StreamBlanker disabled!')
            for idx, source_name in enumerate(sources):
                source = spawn_source('sb-{}'.format(source_name),
                                      Port.SOURCES_BLANK + idx,
                                      has_audio=False)
                self.bins.append(source)
                self.ports.append(Port('sb-{}'.format(source_name), source))

            source = spawn_source('sb',
                                  Port.AUDIO_SOURCE_BLANK,
                                  has_video=False,
                                  force_num_streams=1)
            self.bins.append(source)
            self.ports.append(Port('sb-audio', source))

            self.log.info('Creating Stream Blanker Mixer')
            self.streamblanker = StreamBlanker()
            self.bins.append(self.streamblanker)

            dest = AVRawOutput('mix-sb', Port.LIVE_OUT)
            self.bins.append(dest)
            self.ports.append(Port('live-mix', dest))

            # check for source preview selection
            if Config.getLivePreviewEnabled():
                # count preview port and create source
                dest = AVPreviewOutput('mix-sb', Port.LIVE_PREVIEW)
                self.bins.append(dest)
                self.ports.append(Port("preview-live-mix", dest))

            if Config.getSlidesSource():
                dest = AVRawOutput('mix-sb-slides', Port.SLIDES_LIVE_OUT)
                self.bins.append(dest)
                self.ports.append(Port('live-slides', dest))

        for bin in self.bins:
            self.log.info("%s\n%s", bin, bin.bin)

        # concatinate pipeline string
        pipeline = "\n\n".join(bin.bin for bin in self.bins)

        try:
            # launch gstreamer pipeline
            self.pipeline = Gst.parse_launch(pipeline)
            self.log.info("pipeline launched successfuly")
        except:
            self.log.error("Can not launch pipeline")
            sys.exit(-1)

        # attach pads
        for bin in self.bins:
            bin.attach(self.pipeline)

        self.pipeline.use_clock(Clock)

        # fetch all queues
        self.queues = self.fetch_elements_by_name(r'^queue-[\w_-]+$')

        self.log.debug('Binding End-of-Stream-Signal on Source-Pipeline')
        self.pipeline.bus.add_signal_watch()
        self.pipeline.bus.connect("message::eos", self.on_eos)
        self.pipeline.bus.connect("message::error", self.on_error)
        self.pipeline.bus.connect(
            "message::state-changed", self.on_state_changed)

        self.draw_pipeline = Args.dot

        self.pipeline.set_state(Gst.State.PLAYING)

    def fetch_elements_by_name(self, regex):
        # fetch all watchdogs
        result = []

        def query(element):
            if re.match(regex, element.get_name()):
                result.append(element)
        self.pipeline.iterate_recurse().foreach(query)
        return result

    def on_eos(self, bus, message):
        self.log.debug('Received End-of-Stream-Signal on Source-Pipeline')

    def on_error(self, bus, message):
        self.log.error('Received Error-Signal on Source-Pipeline')
        (error, debug) = message.parse_error()
        self.log.debug('Error-Details: #%u: %s', error.code, debug)

    def on_state_changed(self, bus, message):
        if self.draw_pipeline and message.parse_state_changed().newstate == Gst.State.PLAYING:
            # make DOT file from pipeline
            gst_generate_dot(self.pipeline, "core.pipeline")
            self.draw_pipeline = False
        elif self.draw_pipeline and message.parse_state_changed().newstate == Gst.State.PAUSED:
            self.draw_pipeline = True
