import logging
import sys

from gi.repository import Gst, Gdk

from lib.args import Args
from lib.config import Config
from lib.clock import Clock
from vocto.port import Port
from vocto.debug import gst_generate_dot

CPU_DECODERS = {
    'h264': 'video/x-h264 ! avdec_h264',
    'jpeg': 'image/jpeg ! jpegdec',
    'mpeg2': 'video/mpeg,mpegversion=2 ! mpeg2dec'
}

VAAPI_DECODERS = {
    'h264': 'vaapih264dec',
    'jpeg': 'vaapijpegdec',
    'mpeg2': 'vaapimpeg2dec',
}


class VideoDisplay(object):
    """Displays a Voctomix-Video-Stream into a GtkWidget"""

    def __init__(self, drawing_area, port, name, width=None, height=None,
                 play_audio=False, level_callback=None):
        self.log = logging.getLogger('VideoDisplay[%u]' % port)
        self.name = name
        self.drawing_area = drawing_area
        self.level_callback = level_callback
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
            if Config.getPreviewVaapi():
                video_decoder = VAAPI_DECODERS[Config.getPreviewDecoder()]
            else:
                video_decoder = CPU_DECODERS[Config.getPreviewDecoder()]

            pipe += """
                    demux-{name}.
                    ! queue
                        name=queue-video-{name}
                    ! {video_decoder}
                    """.format(name=name,
                               video_decoder=video_decoder)
        else:
            video_decoder = None
            preview_caps = 'video/x-raw'
            self.log.info('using raw-video instead of encoded-previews')
            pipe += """
                    demux-{name}.
                    ! queue
                        name=queue-video-{name}
                    ! {previewcaps}
                    ! {vcaps}
                    """.format(name=name,
                               previewcaps=preview_caps,
                               vcaps=Config.getVideoCaps())

        if Config.getPreviewNameOverlay() and name:
            textoverlay = """
                        ! textoverlay
                            name=title-{name}
                            text=\"{name}\"
                            valignment=bottom
                            halignment=center
                            shaded-background=yes
                            font-desc="Roboto, 22" 
                        """.format(name=name)
        else:
            textoverlay = ""
        pipe += textoverlay

        # Video Display
        videosystem = Config.getVideoSystem()
        self.log.debug('Configuring for Video-System %s', videosystem)

        pipe += """
                ! videoconvert
                ! videoscale
                """

        if videosystem == 'gl':
            pipe += """
                    ! glupload
                    ! glcolorconvert
                    ! glimagesinkelement
                        name=imagesink-{name}
                    """.format(name=name)

        elif videosystem == 'xv':
            pipe += """
                    ! xvimagesink
                        name=imagesink-{name}
                    """.format(name=name)

        elif videosystem == 'x':
            #if width and height:
                #prescale_caps = 'width=%u,height=%u' % (width, height)
                #pipe += """
                #    ! {prescale_caps}
                #    """.format(prescale_caps=prescale_caps)

            pipe += """
                ! ximagesink
                    name=imagesink-{name}
                """.format(name=name)
        else:
            raise Exception(
                'Invalid Videodisplay-System configured: %s' % videosystem
            )

        # If Playback is requested, push fo pulseaudio
        if play_audio:
            # add an Audio-Path through a level-Element
            pipe += """
                    demux-{name}.
                    ! queue
                        name=queue-audio-{name}
                    ! {acaps}
                    ! level
                        name=lvl
                        interval=50000000
                    ! audioconvert
                    ! pulsesink
                        name=audiosink-{name}"""

        pipe = pipe.format(name=name,
                           acaps=Config.getAudioCaps(),
                           port=port,
                           )

        self.log.info('Creating Display-Pipeline:\n%s', pipe)
        try:
            # launch gstreamer pipeline
            self.pipeline = Gst.parse_launch(pipe)
            self.log.info("pipeline launched successfuly")
        except:
            self.log.error("Can not launch pipeline")
            sys.exit(-1)

        if Args.dot:
            self.log.debug('Generating DOT image of videodisplay pipeline')
            gst_generate_dot(self.pipeline, "gui.videodisplay.{}".format(name))

        self.pipeline.use_clock(Clock)

        self.drawing_area.add_events(
            Gdk.EventMask.KEY_PRESS_MASK | Gdk.EventMask.KEY_RELEASE_MASK)
        self.drawing_area.connect("realize", self.on_realize)
        self.drawing_area.realize()

        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emission()

        bus.connect('message::error', self.on_error)
        bus.connect("sync-message::element", self.on_syncmsg)
        self.pipeline.bus.connect(
            "message::state-changed", self.on_state_changed)

        if self.level_callback:
            bus.connect("message::element", self.on_level)

    def on_realize(self, win):
        self.imagesink = self.pipeline.get_by_name(
            'imagesink-{name}'.format(name=self.name))
        self.xid = self.drawing_area.get_property('window').get_xid()
        self.log.debug('Realized Drawing-Area with xid %u', self.xid)

        self.log.debug('Launching Display-Pipeline')
        self.pipeline.set_state(Gst.State.PLAYING)

    def on_syncmsg(self, bus, msg):
        if type(msg) == Gst.Message and self.imagesink:
            if msg.get_structure().get_name() == "prepare-window-handle":
                self.log.info(
                    'Setting imagesink window-handle to %s', self.xid)
                self.imagesink.set_window_handle(self.xid)

    def on_error(self, bus, message):
        (error, debug) = message.parse_error()
        self.log.error(
            "GStreamer pipeline element '%s' signaled an error #%u: %s" % (message.src.name, error.code, error.message))

    def mute(self, mute):
        self.pipeline.get_by_name("audiosink-{name}".format(name=self.name)).set_property(
            "volume", 1 if mute else 0)

    def on_level(self, bus, msg):
        if msg.src.name != 'lvl':
            return

        if msg.type != Gst.MessageType.ELEMENT:
            return

        rms = msg.get_structure().get_value('rms')
        peak = msg.get_structure().get_value('peak')
        decay = msg.get_structure().get_value('decay')
        self.level_callback(rms, peak, decay)

    def on_state_changed(self, bus, message):
        if message.parse_state_changed().newstate == Gst.State.PLAYING:
            self.drawing_area.show()
