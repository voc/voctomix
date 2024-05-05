import logging
import sys

from gi.repository import Gdk, Gst
from lib.args import Args
from lib.clock import Clock
from lib.config import Config

from vocto.debug import gst_generate_dot
from vocto.port import Port
from vocto.pretty import pretty
from vocto.video_codecs import construct_video_decoder_pipeline


class VideoDisplay(object):
    """Displays a Voctomix-Video-Stream into a GtkWidget"""

    def __init__(
        self,
        video_drawing_area,
        audio_display,
        port,
        name,
        width=None,
        height=None,
        play_audio=False,
    ):
        self.log = logging.getLogger('VideoDisplay:%s' % name)
        self.name = name
        self.video_drawing_area = video_drawing_area
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
                """.format(
            name=name, host=Config.getHost(), port=port
        )

        if Config.getPreviewsEnabled():
            self.log.info('using encoded previews instead of raw-video')

            pipe += """
                demux-{name}.
                ! queue
                    name=queue-video-{name}
                ! {video_decoder}
                """.format(
                name=name, video_decoder=construct_video_decoder_pipeline('previews')
            )

        else:
            video_decoder = None
            preview_caps = 'video/x-raw'
            self.log.info('using raw-video instead of encoded-previews')
            pipe += """
                demux-{name}.
                ! queue
                    name=queue-video-{name}
                ! {previewcaps}
                """.format(
                name=name, previewcaps=preview_caps, vcaps=Config.getVideoCaps()
            )

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
                """.format(
                name=name
            )

        # Video Display
        videosystem = Config.getVideoSystem()
        self.log.debug('Configuring for Video-System %s', videosystem)

        if videosystem == 'gl':
            pipe += """ ! glupload
                        ! glcolorconvert
                        ! glimagesinkelement
                            name=imagesink-{name}
                            """.format(
                name=name
            )

        elif videosystem == 'xv':
            pipe += """ ! xvimagesink
                            name=imagesink-{name}
                        """.format(
                name=name
            )

        elif videosystem == 'x':
            pipe += """ ! ximagesink
                            name=imagesink-{name}
                        """.format(
                name=name
            )

        elif videosystem == 'vaapi':
            pipe += """ ! vaapisink
                            name=imagesink-{name}
                        """.format(
                name=name
            )

        else:
            raise Exception('Invalid Videodisplay-System configured: %s' % videosystem)

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
        pipe = pipe.format(
            name=name,
            acaps=Config.getAudioCaps(),
            port=port,
        )

        self.log.info("Creating Display-Pipeline:\n%s", pretty(pipe))
        try:
            # launch gstreamer pipeline
            self.pipeline = Gst.parse_launch(pipe)
            self.log.info("pipeline launched successfuly")
        except Exception:
            self.log.exception("Can not launch pipeline")
            sys.exit(-1)

        if Args.dot:
            self.log.debug("Generating DOT image of videodisplay pipeline")
            gst_generate_dot(self.pipeline, "gui.videodisplay.{}".format(name))

        self.pipeline.use_clock(Clock)

        self.video_drawing_area.add_events(
            Gdk.EventMask.KEY_PRESS_MASK | Gdk.EventMask.KEY_RELEASE_MASK
        )
        self.video_drawing_area.connect("realize", self.on_realize)
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emission()

        bus.connect('message::error', self.on_error)
        bus.connect('sync-message::element', self.on_syncmsg)
        bus.connect('message::state-changed', self.on_state_changed)
        bus.connect("message::element", self.on_level)

    def on_realize(self, win):
        self.imagesink = self.pipeline.get_by_name(
            'imagesink-{name}'.format(name=self.name)
        )
        self.xid = self.video_drawing_area.get_property('window').get_xid()

        self.log.debug('Realized Drawing-Area with xid %u', self.xid)
        self.video_drawing_area.realize()

        self.log.info("Launching Display-Pipeline")
        self.pipeline.set_state(Gst.State.PLAYING)

    def on_syncmsg(self, bus, msg):
        if isinstance(msg, Gst.Message) and self.imagesink:
            if msg.get_structure().get_name() == "prepare-window-handle":
                self.log.info('Setting imagesink window-handle to 0x%x', self.xid)
                self.imagesink.set_window_handle(self.xid)

    def on_error(self, bus, message):
        (error, debug) = message.parse_error()
        self.log.error(
            "GStreamer pipeline element '%s' signaled an error #%u: %s"
            % (message.src.name, error.code, error.message)
        )

    def mute(self, mute):
        self.pipeline.get_by_name(
            "audiosink-{name}".format(name=self.name)
        ).set_property("volume", 1 if mute else 0)

    def on_level(self, bus, msg):
        if self.level_callback and msg.src.name == 'lvl':
            rms = msg.get_structure().get_value('rms')
            peak = msg.get_structure().get_value('peak')
            decay = msg.get_structure().get_value('decay')
            self.level_callback(rms, peak, decay)

    def on_state_changed(self, bus, message):
        if message.parse_state_changed().newstate == Gst.State.PLAYING:
            self.video_drawing_area.show()
