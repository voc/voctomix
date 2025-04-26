import logging
import sys
from typing import cast

from gi.repository import Gst, Gdk, Gtk

from voctogui.lib.args import Args
from voctogui.lib.config import Config
from voctogui.lib.clock import Clock

from vocto.port import Port
from vocto.debug import gst_generate_dot
from vocto.pretty import pretty
from vocto.video_codecs import construct_video_decoder_pipeline


class VideoDisplay(object):
    """Displays a Voctomix-Video-Stream into a GtkWidget"""
    imagesink: Gst.Element
    widget: Gtk.Widget
    pipeline: Gst.Pipeline

    def __init__(self, audio_display, port, name, width=None, height=None,
                 has_audio=True, play_audio=False):
        self.log = logging.getLogger('VideoDisplay:%s' % name)
        self.name = name
        self.level_callback = None if audio_display is None else audio_display.callback
        video_decoder = None

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

        if Config.getPreviewsEnabled():
            self.log.info('using encoded previews instead of raw-video')

            pipe += """
                demux-{name}.
                ! queue
                    name=queue-video-{name}
                ! {video_decoder}
                """.format(name=name,
                           video_decoder=construct_video_decoder_pipeline(Config, 'previews'))

        else:
            video_decoder = None
            preview_caps = 'video/x-raw'
            self.log.info('using raw-video instead of encoded-previews')
            pipe += """
                demux-{name}.
                ! queue
                    name=queue-video-{name}
                ! {previewcaps}
                """.format(name=name,
                           previewcaps=preview_caps)

        pipe += """ ! videoconvert
                    ! videoscale
                    """

        if Config.getPreviewNameOverlay() and name:
            pipe += """\
                ! textoverlay
                    name=title-{name}
                    text=\"{name}\"
                    valignment=bottom
                    halignment=center
                    shaded-background=yes
                    font-desc="Roboto, 22"
                """.format(name=name)

        # Video Display
        videosystem = Config.getVideoSystem()
        self.log.debug('Configuring for Video-System %s', videosystem)
        if videosystem == 'gtk':
            pipe += """ ! gtksink
                            name=imagesink-{name} sync=false
                """.format(name=name)

        elif videosystem == 'gtkgl':
            pipe += """ ! glupload
                        ! gtkglsink
                            name=imagesink-{name} sync=false
                """.format(name=name)

        else:
            raise Exception(
                'Invalid Videodisplay-System configured: %s' % videosystem
            )

        if has_audio:
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
            self.pipeline = cast(Gst.Pipeline, Gst.parse_launch(pipe))
            self.log.info("pipeline launched successfuly")
        except:
            self.log.error("Can not launch pipeline")
            sys.exit(-1)

        self.imagesink = cast(Gst.Element, self.pipeline.get_by_name('imagesink-{name}'.format(name=self.name)))
        self.widget = cast(Gtk.Widget, self.imagesink.get_property("widget"))

        if Args.dot:
            self.log.debug("Generating DOT image of videodisplay pipeline")
            gst_generate_dot(self.pipeline, "gui.videodisplay.{}".format(name), Args.gst_debug_details)

        self.pipeline.set_clock(Clock)
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emission()

        bus.connect('message::error', self.on_error)
        bus.connect("message::element", self.on_level)

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

    def play(self):
        self.pipeline.set_state(Gst.State.PLAYING)
