import logging
from gi.repository import Gst

from lib.config import Config
from lib.tcpmulticonnection import TCPMultiConnection
from lib.clock import Clock


class AVPreviewOutput(TCPMultiConnection):

    def __init__(self, channel, port):
        self.log = logging.getLogger('AVPreviewOutput[{}]'.format(channel))
        super().__init__(port)

        self.channel = channel

        if Config.has_option('previews', 'videocaps'):
            target_caps = Config.get('previews', 'videocaps')
        else:
            target_caps = Config.get('mix', 'videocaps')

        pipeline = """
            intervideosrc channel=video_{channel} !
            {vcaps} !
            {vpipeline} !
            queue !
            mux.

            interaudiosrc channel=audio_{channel} !
            {acaps} !
            queue !
            mux.

            matroskamux
                name=mux
                streamable=true
                writing-app=Voctomix-AVPreviewOutput !

            multifdsink
                blocksize=1048576
                buffers-max=500
                sync-method=next-keyframe
                name=fd
        """.format(
            channel=self.channel,
            acaps=Config.get('mix', 'audiocaps'),
            vcaps=Config.get('mix', 'videocaps'),
            vpipeline=self.construct_video_pipeline(target_caps)
        )

        self.log.debug('Creating Output-Pipeline:\n%s', pipeline)
        self.outputPipeline = Gst.parse_launch(pipeline)
        self.outputPipeline.use_clock(Clock)

        self.log.debug('Binding Error & End-of-Stream-Signal '
                       'on Output-Pipeline')
        self.outputPipeline.bus.add_signal_watch()
        self.outputPipeline.bus.connect("message::eos", self.on_eos)
        self.outputPipeline.bus.connect("message::error", self.on_error)

        self.log.debug('Launching Output-Pipeline')
        self.outputPipeline.set_state(Gst.State.PLAYING)

    def construct_video_pipeline(self, target_caps):
        vaapi_enabled = Config.has_option('previews', 'vaapi')
        if vaapi_enabled:
            return self.construct_vaapi_video_pipeline(target_caps)

        else:
            return self.construct_native_video_pipeline(target_caps)

    def construct_vaapi_video_pipeline(self, target_caps):
        if Gst.version() < (1, 8):
            vaapi_encoders = {
                'h264': 'vaapiencode_h264',
                'jpeg': 'vaapiencode_jpeg',
                'mpeg2': 'vaapiencode_mpeg2',
            }
        else:
            vaapi_encoders = {
                'h264': 'vaapih264enc',
                'jpeg': 'vaapijpegenc',
                'mpeg2': 'vaapimpeg2enc',
            }

        vaapi_encoder_options = {
            'h264': 'rate-control=cqp init-qp=10 '
                    'max-bframes=0 keyframe-period=60',
            'jpeg': 'vaapiencode_jpeg quality=90'
                    'keyframe-period=0',
            'mpeg2': 'keyframe-period=60',
        }

        encoder = Config.get('previews', 'vaapi')
        do_deinterlace = Config.getboolean('previews', 'deinterlace')

        caps = Gst.Caps.from_string(target_caps)
        struct = caps.get_structure(0)
        _, width = struct.get_int('width')
        _, height = struct.get_int('height')
        _, framerate_numerator, framerate_denominator = struct.get_fraction('framerate')


        return '''
            capsfilter caps=video/x-raw,interlace-mode=progressive !
            vaapipostproc
                format=i420
                deinterlace-mode={imode}
                deinterlace-method=motion-adaptive
                width={width}
                height={height} !
            capssetter caps=video/x-raw,framerate={n}/{d} !
            {encoder} {options}
        '''.format(
            imode='interlaced' if do_deinterlace else 'disabled',
            width=width,
            height=height,
            encoder=vaapi_encoders[encoder],
            options=vaapi_encoder_options[encoder],
            n=framerate_numerator,
            d=framerate_denominator,
        )

    def construct_native_video_pipeline(self, target_caps):
        do_deinterlace = Config.getboolean('previews', 'deinterlace')

        if do_deinterlace:
            pipeline = '''
                deinterlace mode={imode} !
                videorate !
            '''
        else:
            pipeline = ''


        pipeline += '''
            videoscale !
            {target_caps} !
            jpegenc quality=90
        '''

        return pipeline.format(
            imode='interlaced' if do_deinterlace else 'disabled',
            target_caps=target_caps,
        )

    def on_accepted(self, conn, addr):
        self.log.debug('Adding fd %u to multifdsink', conn.fileno())
        fdsink = self.outputPipeline.get_by_name('fd')
        fdsink.emit('add', conn.fileno())

        def on_disconnect(multifdsink, fileno):
            if fileno == conn.fileno():
                self.log.debug('fd %u removed from multifdsink', fileno)
                self.close_connection(conn)

        fdsink.connect('client-fd-removed', on_disconnect)

    def on_eos(self, bus, message):
        self.log.debug('Received End-of-Stream-Signal on Output-Pipeline')

    def on_error(self, bus, message):
        self.log.debug('Received Error-Signal on Output-Pipeline')
        (error, debug) = message.parse_error()
        self.log.debug('Error-Details: #%u: %s', error.code, debug)
