import logging
from gi.repository import Gst

from lib.config import Config
from lib.tcpmulticonnection import TCPMultiConnection
from lib.clock import Clock

class AVPreviewOutput(TCPMultiConnection):
	def __init__(self, channel, port):
		self.log = logging.getLogger('AVPreviewOutput['+channel+']')
		super().__init__(port)

		self.channel = channel

		if Config.has_option('previews', 'videocaps'):
			vcaps_out = Config.get('previews', 'videocaps')
		else:
			vcaps_out = Config.get('mix', 'videocaps')

		deinterlace = ""
		if Config.getboolean('previews', 'deinterlace'):
			deinterlace = "deinterlace mode=interlaced !"

		pipeline = """
			intervideosrc channel=video_{channel} !
			{vcaps_in} !
			{deinterlace}
			videoscale !
			videorate !
			{vcaps_out} !
			jpegenc quality=90 !
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
			vcaps_in=Config.get('mix', 'videocaps'),
			vcaps_out=vcaps_out,
			deinterlace=deinterlace
		)

		self.log.debug('Creating Output-Pipeline:\n%s', pipeline)
		self.outputPipeline = Gst.parse_launch(pipeline)
		self.outputPipeline.use_clock(Clock)

		self.log.debug('Binding Error & End-of-Stream-Signal on Output-Pipeline')
		self.outputPipeline.bus.add_signal_watch()
		self.outputPipeline.bus.connect("message::eos", self.on_eos)
		self.outputPipeline.bus.connect("message::error", self.on_error)

		self.log.debug('Launching Output-Pipeline')
		self.outputPipeline.set_state(Gst.State.PLAYING)

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
