#!/usr/bin/python3
import logging, socket
from gi.repository import GObject, Gst

from lib.config import Config

class AudioSrc(object):
	log = logging.getLogger('AudioSrc')

	name = None
	port = None
	caps = None

	receiverPipeline = None

	boundSocket = None
	currentConnection = None

	def __init__(self, name, port, caps):
		self.log = logging.getLogger('AudioSrc['+name+']')

		self.name = name
		self.port = port
		self.caps = caps

		self.log.debug('Binding to Source-Socket on [::]:%u', port)
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

		if self.currentConnection is not None:
			self.log.warn("Another Source is already connected")
			return True

		pipeline = """
			fdsrc fd={fd} !
			gdpdepay !
			{caps} !
			queue !
			tee name=tee

			tee. ! queue ! interaudiosink channel=audio_{name}_mixer
			tee. ! queue ! interaudiosink channel=audio_{name}_mirror
		""".format(
			fd=conn.fileno(),
			name=self.name,
			caps=self.caps
		)
		self.log.debug('Launching Source-Receiver-Pipeline:\n%s', pipeline)
		self.receiverPipeline = Gst.parse_launch(pipeline)

		self.log.debug('Binding End-of-Stream-Signal on Source-Receiver-Pipeline')
		self.receiverPipeline.bus.add_signal_watch()
		self.receiverPipeline.bus.connect("message::eos", self.on_eos)
		self.receiverPipeline.bus.connect("message::error", self.on_error)

		self.receiverPipeline.set_state(Gst.State.PLAYING)

		self.currentConnection = conn
		return True

	def on_eos(self, bus, message):
		self.log.info('Received End-of-Stream-Signal on Source-Receiver-Pipeline')
		if self.currentConnection is not None:
			self.disconnect()

	def on_error(self, bus, message):
		self.log.info('Received Error-Signal on Source-Receiver-Pipeline')
		(code, debug) = message.parse_error()
		self.log.debug('Error-Details: #%u: %s', code, debug)

		if self.currentConnection is not None:
			self.disconnect()

	def disconnect(self):
		self.receiverPipeline.set_state(Gst.State.NULL)
		self.receiverPipeline = None
		self.currentConnection = None
