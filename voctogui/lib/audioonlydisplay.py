import logging
import sys

from gi.repository import Gst, Gdk

from lib.args import Args
from lib.config import Config
from lib.clock import Clock

from vocto.port import Port
from vocto.debug import gst_generate_dot
from vocto.pretty import pretty

class AudioOnlyDisplay(object):
    """Displays a Voctomix-AudioOnly-Stream into a GtkWidget"""

    def __init__(self, audio_display, port, name, play_audio=False):
        self.log = logging.getLogger('AudioOnlyDisplay:%s' % name)
        self.name = name
        self.level_callback = None if audio_display is None else audio_display.callback

        # Setup Server-Connection, Demuxing and Decoding
        pipe = """
            tcpclientsrc
                name=tcpsrc-{name}
                host={host}
                port={port}
                blocksize=1048576
            ! matroskademux
                name=demux-{name}
                """.format(name=name,
                           host=Config.getHost(),
                           port=port)

        # add an Audio-Path through a level-Element
        pipe += """
            demux-{name}.
            ! queue
                name=queue-audio-{name}
            ! level
                name=lvl
                interval=50000000
            ! audioconvert
            """

        # If Playback is requested, push fo pulseaudio
        if play_audio:
            pipe += """ ! pulsesink
                            name=audiosink-{name}
                        """
        else:
            pipe += """ ! fakesink
                        """
        pipe = pipe.format(name=name,
                           acaps=Config.getAudioCaps(),
                           port=port,
                           )

        self.log.info("Creating Display-Pipeline:\n%s",  pretty(pipe))
        try:
            # launch gstreamer pipeline
            self.pipeline = Gst.parse_launch(pipe)
            self.log.info("pipeline launched successfuly")
        except:
            self.log.error("Can not launch pipeline")
            sys.exit(-1)

        if Args.dot:
            self.log.debug("Generating DOT image of audioonlydisplay pipeline")
            gst_generate_dot(self.pipeline, "gui.audioonlydisplay.{}".format(name), Args.gst_debug_details)

        self.pipeline.use_clock(Clock)

        bus = self.pipeline.get_bus()
        bus.add_signal_watch()

        bus.connect('message::error', self.on_error)
        bus.connect("message::element", self.on_level)
        
        self.log.info("Launching Display-Pipeline")
        self.pipeline.set_state(Gst.State.PLAYING)

    def on_error(self, bus, message):
        (error, debug) = message.parse_error()
        self.log.error(
            "GStreamer pipeline element '%s' signaled an error #%u: %s" % (message.src.name, error.code, error.message))

    def mute(self, mute):
        self.pipeline.get_by_name("audiosink-{name}".format(name=self.name)).set_property(
            "volume", 1 if mute else 0)

    def on_level(self, bus, msg):
        if self.level_callback and msg.src.name == 'lvl':
            rms = msg.get_structure().get_value('rms')
            peak = msg.get_structure().get_value('peak')
            decay = msg.get_structure().get_value('decay')
            self.level_callback(rms, peak, decay)
