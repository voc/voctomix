#!/usr/bin/python3
import logging
from gi.repository import Gst

from lib.config import Config
from lib.tcpmulticonnection import TCPMultiConnection

class AVPreviewOutput(TCPMultiConnection):
	def __init__(self, channel, port):
		self.log = logging.getLogger('AVPreviewOutput['+channel+']')
		super().__init__(port)

		self.channel = channel

		if Config.has_option('previews', 'videocaps'):
			vcaps_out = Config.get('previews', 'videocaps')
		else:
			vcaps_out = Config.get('mix', 'videocaps')

		pipeline = """
			interaudiosrc channel=audio_{channel} !
			{acaps} !
			queue !
			mux.

			intervideosrc channel=video_{channel} !
			{vcaps_in} !
			videorate !
			videoscale method=nearest-neighbour !
			{vcaps_out} !
			jpegenc !
			queue !
			mux.

			matroskamux
				name=mux
				streamable=true
				writing-app=Voctomix-AVPreviewOutput !

			multifdsink
				sync-method=next-keyframe
				name=fd
		""".format(
			channel=self.channel,
			acaps=Config.get('mix', 'audiocaps'),
			vcaps_in=Config.get('mix', 'videocaps'),
			vcaps_out=vcaps_out
		)

		self.log.debug('Launching Output-Pipeline:\n%s', pipeline)
		self.receiverPipeline = Gst.parse_launch(pipeline)
		self.receiverPipeline.set_state(Gst.State.PLAYING)

	def on_accepted(self, conn):
		self.log.debug('Adding fd %u to multifdsink', conn.fileno())
		fdsink = self.receiverPipeline.get_by_name('fd')
		fdsink.emit('add', conn.fileno())

		def on_disconnect(multifdsink, fileno):
			if fileno == conn.fileno():
				self.log.debug('fd %u removed from multifdsink', fileno)
				self.close_connection(conn)

		fdsink.connect('client-fd-removed', on_disconnect)
