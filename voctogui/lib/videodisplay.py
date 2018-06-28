import logging
import re
from gi.repository import Gst

from lib.args import Args
from lib.config import Config
from lib.clock import Clock


class VideoDisplay(object):
    """Displays a Voctomix-Video-Stream into a GtkWidget"""

    def __init__(self, drawing_area, port, width=None, height=None,
                 play_audio=False, level_callback=None):
        self.log = logging.getLogger('VideoDisplay[%u]' % port)

        self.drawing_area = drawing_area
        self.level_callback = level_callback

        if Config.has_option('previews', 'videocaps'):
            previewcaps = Config.get('previews', 'videocaps')
        else:
            previewcaps = Config.get('mix', 'videocaps')

        use_previews = Config.getboolean('previews', 'enabled') \
            and Config.getboolean('previews', 'use')

        audiostreams = int(Config.get('mix', 'audiostreams'))

        if (Config.get('mainvideo', 'vumeter') != 'all') \
                and int(Config.get('mainvideo', 'vumeter')) < audiostreams:
            audiostreams = int(Config.get('mainvideo', 'vumeter'))

        # Preview-Ports are Raw-Ports + 1000
        if use_previews:
            self.log.info('using encoded previews instead of raw-video')
            port += 1000

            vdec = 'image/jpeg ! jpegdec'
            if Config.has_option('previews', 'vaapi'):
                try:
                    decoder = Config.get('previews', 'vaapi')
                    decoders = {
                        'h264': 'video/x-h264 ! avdec_h264',
                        'jpeg': 'image/jpeg ! jpegdec',
                        'mpeg2': 'video/mpeg,mpegversion=2 ! mpeg2dec'
                    }
                    vdec = decoders[decoder]
                except Exception as e:
                    self.log.error(e)

        else:
            self.log.info('using raw-video instead of encoded-previews')
            vdec = None

        # Setup Server-Connection, Demuxing and Decoding
        pipeline = """
            tcpclientsrc host={host} port={port} blocksize=1048576 !
            queue !
            matroskademux name=demux
        """

        if use_previews:
            pipeline += """
                demux. !
                {vdec} !
                {previewcaps} !
                queue !
            """

        else:
            pipeline += """
                demux. !
                {vcaps} !
                queue !
            """

        # Video Display
        videosystem = Config.get('videodisplay', 'system')
        self.log.debug('Configuring for Video-System %s', videosystem)
        if videosystem == 'gl':
            pipeline += """
                glupload !
                glcolorconvert !
                glimagesinkelement
            """

        elif videosystem == 'xv':
            pipeline += """
                xvimagesink
            """

        elif videosystem == 'x':
            prescale_caps = 'video/x-raw'
            if width and height:
                prescale_caps += ',width=%u,height=%u' % (width, height)

            pipeline += """
                videoconvert !
                videoscale !
                {prescale_caps} !
                ximagesink
            """.format(prescale_caps=prescale_caps)

        else:
            raise Exception(
                'Invalid Videodisplay-System configured: %s' % videosystem
            )

        # If an Audio-Path is required,
        # add an Audio-Path through a level-Element
        if self.level_callback or play_audio:
            for audiostream in range(0, audiostreams):
                pipeline += """
                    demux.audio_{audiostream} !
                """.format(audiostream=audiostream)
                pipeline += """
                    {acaps} !
                    queue !
                    """
                pipeline += """
                    level name=lvl_{audiostream} interval=50000000 !
                """.format(audiostream=audiostream)

                # If Playback is requested, push fo pulseaudio
                if play_audio and audiostream == 0:
                    pipeline += """
                        pulsesink
                    """

                # Otherwise just trash the Audio
                else:
                    pipeline += """
                        fakesink
                    """

        pipeline = pipeline.format(
            acaps=Config.get('mix', 'audiocaps'),
            vcaps=Config.get('mix', 'videocaps'),
            previewcaps=previewcaps,
            host=Args.host if Args.host else Config.get('server', 'host'),
            vdec=vdec,
            port=port,
        )

        self.log.debug('Creating Display-Pipeline:\n%s', pipeline)
        self.pipeline = Gst.parse_launch(pipeline)
        self.pipeline.use_clock(Clock)

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
        self.log.debug('Received Error-Signal on Display-Pipeline')
        (error, debug) = message.parse_error()
        self.log.debug('Error-Details: #%u: %s', error.code, debug)

    def on_level(self, bus, msg):
        if not(msg.src.name.startswith('lvl_')):
            return

        if msg.type != Gst.MessageType.ELEMENT:
            return

        rms = msg.get_structure().get_value('rms')
        peak = msg.get_structure().get_value('peak')
        decay = msg.get_structure().get_value('decay')
        stream = int(msg.src.name[4])
        self.level_callback(rms, peak, decay, stream)
