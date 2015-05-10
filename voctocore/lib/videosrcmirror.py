#!/usr/bin/python3
import logging, socket
from gi.repository import GObject, Gst

from lib.config import Config

class VideoSrcMirror(object):
	log = logging.getLogger('VideoSrcMirror')

	name = None
	port = None
	caps = None

	boundSocket = None

	receiverPipelines = []
	currentConnections = []

	def __init__(self, name, port, caps):
		self.log = logging.getLogger('VideoSrcMirror['+name+']')

		self.name = name
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
		self.log.info("incomming connection from %s", addr)

		pipeline = """
			intervideosrc channel={name}_mirror !
			{caps} !
			textoverlay text={name}_mirror halignment=left valignment=top ypad=125 !
			gdppay !
			fdsink fd={fd}
		""".format(
			fd=conn.fileno(),
			name=self.name,
			caps=self.caps
		)
		self.log.debug('Launching Mirror-Receiver-Pipeline:\n%s', pipeline)
		receiverPipeline = Gst.parse_launch(pipeline)

		self.log.debug('Binding End-of-Stream-Signal on Source-Receiver-Pipeline')
		receiverPipeline.bus.add_signal_watch()
		receiverPipeline.bus.connect("message::eos", self.on_disconnect)

		receiverPipeline.set_state(Gst.State.PLAYING)

		self.receiverPipelines.append(receiverPipeline)
		self.currentConnections.append(conn)

		return True

	def on_disconnect(self, bus, message):
		self.log.info('Received End-of-Stream-Signal on Source-Receiver-Pipeline')
