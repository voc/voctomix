#!/usr/bin/python3
import logging, socket
from gi.repository import GObject, Gst

from lib.config import Config

class AVRawOutput(object):
	log = logging.getLogger('AVRawOutput')

	name = None
	port = None
	caps = None

	boundSocket = None
	receiverPipeline = None

	currentConnections = []

	def __init__(self, channel, port):
		self.log = logging.getLogger('AVRawOutput['+channel+']')

		self.channel = channel
		self.port = port

		pipeline = """
			interaudiosrc channel=audio_{channel} !
			{acaps} !
			queue !
			mux.

			intervideosrc channel=video_{channel} !
			{vcaps} !
			textoverlay halignment=left valignment=top ypad=75 text=AVRawOutput !
			timeoverlay halignment=left valignment=top ypad=75 xpad=400 !
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
		self.receiverPipeline.bus.add_signal_watch()
		self.receiverPipeline.set_state(Gst.State.PLAYING)

		self.log.debug('Binding to Output-Socket on [::]:%u', port)
		self.boundSocket = socket.socket(socket.AF_INET6)
		self.boundSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.boundSocket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, False)
		self.boundSocket.bind(('::', port))
		self.boundSocket.listen(1)

		self.log.debug('Setting GObject io-watch on Socket')
		GObject.io_add_watch(self.boundSocket, GObject.IO_IN, self.on_connect)

	def on_connect(self, sock, *args):
		conn, addr = sock.accept()
		self.log.info("Incomming Connection from %s", addr)

		self.log.info('Adding fd %u to multifdsink', conn.fileno())
		self.receiverPipeline.get_by_name('fd').emit('add', conn.fileno())

		self.currentConnections.append(conn)
		self.log.info('Now %u Receiver connected', len(self.currentConnections))

		return True

	# FIXME handle disconnects
	def disconnect(self, receiverPipeline, currentConnection):
		self.currentConnections.remove(currentConnection)
		self.log.info('Disconnected Receiver, now %u Receiver connected', len(self.currentConnections))
