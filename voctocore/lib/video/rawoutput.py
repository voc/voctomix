#!/usr/bin/python3
import logging, socket
from gi.repository import GObject, Gst

from lib.config import Config

class VideoRawOutput(object):
	log = logging.getLogger('VideoRawOutput')

	name = None
	port = None
	caps = None

	boundSocket = None

	receiverPipelines = []
	currentConnections = []

	def __init__(self, channel, port, caps):
		self.log = logging.getLogger('VideoRawOutput['+channel+']')

		self.channel = channel
		self.port = port
		self.caps = caps

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

		pipeline = """
			intervideosrc channel={channel} !
			{caps} !
			textoverlay text={channel} halignment=left valignment=top ypad=225 !
			gdppay !
			fdsink fd={fd}
		""".format(
			fd=conn.fileno(),
			channel=self.channel,
			caps=self.caps
		)
		self.log.debug('Launching Pipeline:\n%s', pipeline)
		receiverPipeline = Gst.parse_launch(pipeline)

		def on_eos(bus, message):
			self.log.info('Received End-of-Stream-Signal on Source-Receiver-Pipeline')
			self.disconnect(receiverPipeline, conn)

		def on_error(bus, message):
			self.log.info('Received Error-Signal on Source-Receiver-Pipeline')

			(error, debug) = message.parse_error()
			self.log.debug('Error-Message %s\n%s', error.message, debug)

			self.disconnect(receiverPipeline, conn)

		self.log.debug('Binding End-of-Stream-Signal on Pipeline')
		receiverPipeline.bus.add_signal_watch()
		receiverPipeline.bus.connect("message::eos", on_eos)
		receiverPipeline.bus.connect("message::error", on_error)

		receiverPipeline.set_state(Gst.State.PLAYING)

		self.receiverPipelines.append(receiverPipeline)
		self.currentConnections.append(conn)

		self.log.info('Now %u Receiver connected', len(self.currentConnections))

		return True

	def disconnect(self, receiverPipeline, currentConnection):
		receiverPipeline.set_state(Gst.State.NULL)
		self.receiverPipelines.remove(receiverPipeline)
		self.currentConnections.remove(currentConnection)
		self.log.info('Disconnected Receiver, now %u Receiver connected', len(self.currentConnections))
