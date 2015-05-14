#!/usr/bin/python3
import logging, socket
from gi.repository import GObject, Gst

from lib.config import Config

class AVSource(object):
	log = logging.getLogger('AVSource')

	name = None
	port = None
	caps = None

	receiverPipeline = None

	boundSocket = None
	currentConnection = None

	def __init__(self, name, port):
		self.log = logging.getLogger('AVSource['+name+']')

		self.name = name
		self.port = port

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
			matroskademux name=demux

			demux. ! 
			{acaps} !
			queue !
			tee name=atee

			atee. ! queue ! interaudiosink channel=audio_{name}_mixer
			atee. ! queue ! interaudiosink channel=audio_{name}_mirror

			demux. ! 
			{vcaps} !
			textoverlay halignment=left valignment=top ypad=25 text=AVSource !
			timeoverlay halignment=left valignment=top ypad=25 xpad=400 !
			queue !
			tee name=vtee

			vtee. ! queue ! intervideosink channel=video_{name}_mixer
			vtee. ! queue ! intervideosink channel=video_{name}_mirror
		""".format(
			fd=conn.fileno(),
			name=self.name,
			acaps=Config.get('mix', 'audiocaps'),
			vcaps=Config.get('mix', 'videocaps')
		)
		self.log.debug('Launching Source-Pipeline:\n%s', pipeline)
		self.receiverPipeline = Gst.parse_launch(pipeline)

		self.log.debug('Binding End-of-Stream-Signal on Source-Pipeline')
		self.receiverPipeline.bus.add_signal_watch()
		self.receiverPipeline.bus.connect("message::eos", self.on_eos)
		self.receiverPipeline.bus.connect("message::error", self.on_error)

		self.receiverPipeline.set_state(Gst.State.PLAYING)

		self.currentConnection = conn
		return True

	def on_eos(self, bus, message):
		self.log.debug('Received End-of-Stream-Signal on Source-Pipeline')
		if self.currentConnection is not None:
			self.disconnect()

	def on_error(self, bus, message):
		self.log.debug('Received Error-Signal on Source-Pipeline')
		(error, debug) = message.parse_error()
		self.log.debug('Error-Details: #%u: %s', error.code, debug)

		if self.currentConnection is not None:
			self.disconnect()

	def disconnect(self):
		self.log.info('Connection closed')
		self.receiverPipeline.set_state(Gst.State.NULL)
		self.receiverPipeline = None
		self.currentConnection = None
