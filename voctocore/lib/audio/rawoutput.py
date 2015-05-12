#!/usr/bin/python3
import logging, socket
from gi.repository import GObject, Gst

from lib.config import Config

class AudioRawOutput(object):
	log = logging.getLogger('AudioRawOutput')

	name = None
	port = None
	caps = None

	boundSocket = None
	receiverPipeline = None

	currentConnections = []

	def __init__(self, channel, port, caps):
		self.log = logging.getLogger('AudioRawOutput['+channel+']')

		self.channel = channel
		self.port = port
		self.caps = caps

		pipeline = """
			interaudiosrc channel={channel} !
			{caps} !
			gdppay !
			multifdsink resend-streamheader=false name=fd
		""".format(
			channel=self.channel,
			caps=self.caps
		)
		self.log.debug('Launching Pipeline:\n%s', pipeline)
		self.receiverPipeline = Gst.parse_launch(pipeline)
		self.receiverPipeline.bus.add_signal_watch()
		self.receiverPipeline.set_state(Gst.State.PLAYING)

		self.log.debug('Binding to Mirror-Socket on [::]:%u', port)
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

	def disconnect(self, receiverPipeline, currentConnection):
		self.currentConnections.remove(currentConnection)
		self.log.info('Disconnected Receiver, now %u Receiver connected', len(self.currentConnections))
