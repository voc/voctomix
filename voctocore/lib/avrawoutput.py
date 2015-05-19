#!/usr/bin/python3
import logging
from gi.repository import Gst

from lib.config import Config
from lib.tcpmulticonnection import TCPMultiConnection

class AVRawOutput(TCPMultiConnection):
	def __init__(self, channel, port):
		self.log = logging.getLogger('AVRawOutput['+channel+']')
		super().__init__(port)

		self.channel = channel

		pipeline = """
			interaudiosrc channel=audio_{channel} !
			{acaps} !
			queue !
			mux.

			intervideosrc channel=video_{channel} !
			{vcaps} !
			queue !
			mux.

			matroskamux
				name=mux
				streamable=true
				writing-app=Voctomix-AVRawOutput !

			multifdsink
				sync-method=next-keyframe
				name=fd
		""".format(
			channel=self.channel,
			acaps=Config.get('mix', 'audiocaps'),
			vcaps=Config.get('mix', 'videocaps')
		)
		self.log.debug('Launching Output-Pipeline:\n%s', pipeline)
		self.receiverPipeline = Gst.parse_launch(pipeline)
		self.receiverPipeline.set_state(Gst.State.PLAYING)

	def on_accepted(self, conn, addr):
		self.log.debug('Adding fd %u to multifdsink', conn.fileno())
		fdsink = self.receiverPipeline.get_by_name('fd')
		fdsink.emit('add', conn.fileno())

		def on_disconnect(multifdsink, fileno):
			if fileno == conn.fileno():
				self.log.debug('fd %u removed from multifdsink', fileno)
				self.close_connection(conn, addr)

		fdsink.connect('client-fd-removed', on_disconnect)
