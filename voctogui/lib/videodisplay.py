import logging
from gi.repository import Gst, Gdk

from lib.args import Args
from lib.config import Config
from lib.clock import Clock
from vocto.port import Port
from vocto.debug import gst_generate_png

DECODERS = {
    'h264': 'video/x-h264 ! avdec_h264',
    'jpeg': 'image/jpeg ! jpegdec',
    'mpeg2': 'video/mpeg,mpegversion=2 ! mpeg2dec'
}

class VideoDisplay(object):
    """Displays a Voctomix-Video-Stream into a GtkWidget"""

    def __init__(self, drawing_area, port, name=None, width=None, height=None,
                 play_audio=False, level_callback=None):
        self.log = logging.getLogger('VideoDisplay[%u]' % port)

        self.drawing_area = drawing_area
        self.level_callback = level_callback

        # Setup Server-Connection, Demuxing and Decoding
        pipe = """
tcpclientsrc
    host={host}
    port={port}
    blocksize=1048576
! matroskademux
    name=demux
        """

        if Config.getUsePreviews():
            self.log.info('using encoded previews instead of raw-video')
            port += Port.OFFSET_PREVIEW
            vdec = DECODERS[Config.getPreviewDecoder()]

            pipe += """
demux.
! queue
! {vdec}
! {previewcaps}"""
        else:
            vdec = None
            self.log.info('using raw-video instead of encoded-previews')
            pipe += """
demux.
! queue
! {vcaps}"""

        if Config.getPreviewNameOverlay() and name:
            textoverlay = """
! textoverlay
    text=\"{name}\"
    valignment=bottom
    halignment=center
    shaded-background=yes
    font-desc="Roboto, 22" """
        else:
            textoverlay = ""

        # Video Display
        videosystem = Config.getVideoSystem()
        self.log.debug('Configuring for Video-System %s', videosystem)
        if videosystem == 'gl':
            pipe += textoverlay + """
! glupload
! glcolorconvert
! glimagesinkelement
            """

        elif videosystem == 'xv':
            pipe += textoverlay + """
! xvimagesink
            """

        elif videosystem == 'x':
            prescale_caps = 'video/x-raw'
            if width and height:
                prescale_caps += ',width=%u,height=%u' % (width, height)

            pipe += """
! videoconvert
! videoscale {textoverlay}
! {prescale_caps}
! ximagesink
            """.format(prescale_caps=prescale_caps, textoverlay=textoverlay)

        else:
            raise Exception(
                'Invalid Videodisplay-System configured: %s' % videosystem
            )

        # add an Audio-Path through a level-Element
        pipe += """
demux.
! queue
! {acaps}
! level
    name=lvl
    interval=50000000
! pulsesink
    name=audiosink"""
        # If Playback is requested, push fo pulseaudio
        if not play_audio:
            pipe += """
    volume=0
            """

        pipe = pipe.format(
            name=name,
            acaps=Config.getAudioCaps(),
            vcaps=Config.getVideoCaps(),
            previewcaps=Config.getPreviewCaps(),
            host=Config.getHost(),
            vdec=vdec,
            port=port,
        )

        self.log.info('Creating Display-Pipeline:\n%s', pipe)
        self.pipeline = Gst.parse_launch(pipe)

        if Args.dot:
            self.log.debug('Generating DOT image of videodisplay pipeline')
            gst_generate_png(self.pipeline, "gui.videodisplay.{}".format(name))

        self.pipeline.use_clock(Clock)

        self.drawing_area.add_events(Gdk.EventMask.KEY_PRESS_MASK|Gdk.EventMask.KEY_RELEASE_MASK)
        self.drawing_area.realize()
        self.xid = self.drawing_area.get_property('window').get_xid()
        self.log.debug('Realized Drawing-Area with xid %u', self.xid)

        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emission()

        bus.connect('message::error', self.on_error)
        bus.connect("sync-message::element", self.on_syncmsg)

        if self.level_callback:
            bus.connect("message::element", self.on_level)

        self.log.debug('Launching Display-Pipeline')
        self.pipeline.set_state(Gst.State.PLAYING)

    def on_syncmsg(self, bus, msg):
        if msg.get_structure().get_name() == "prepare-window-handle":
            self.log.info('Setting imagesink window-handle to %s', self.xid)
            msg.src.set_window_handle(self.xid)

    def on_error(self, bus, message):
        self.log.error('Received Error-Signal on Display-Pipeline')
        (error, debug) = message.parse_error()
        self.log.debug('Error-Details: #%u: %s', error.code, debug)

    def mute(self, mute):
        self.pipeline.get_by_name("audiosink").set_property("volume",1 if mute else 0)

    def on_level(self, bus, msg):
        if msg.src.name != 'lvl':
            return

        if msg.type != Gst.MessageType.ELEMENT:
            return

        rms = msg.get_structure().get_value('rms')
        peak = msg.get_structure().get_value('peak')
        decay = msg.get_structure().get_value('decay')
        self.level_callback(rms, peak, decay)
