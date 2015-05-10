#!/usr/bin/python3
import logging, socket
from gi.repository import GObject, Gst

from lib.config import Config

class VideoSrc(object):
	log = logging.getLogger('VideoSrc')

	name = None
	port = None
	caps = None

	distributionPipeline = None
	receiverPipeline = None

	boundSocket = None
	currentConnection = None

	def __init__(self, name, port, caps):
		self.log = logging.getLogger('VideoSrc['+name+']')

		self.name = name
		self.port = port
		self.caps = caps

		pipeline = """
			intervideosrc channel={name}_in !
			{caps} !
			timeoverlay halignment=left valignment=top !
			textoverlay text={name}_in halignment=left valignment=top ypad=75 !
			queue !
			tee name=tee

			tee. ! queue ! intervideosink channel={name}_mirror
			tee. ! queue ! intervideosink channel={name}_preview
			tee. ! queue ! intervideosink channel={name}_mixer
		""".format(
			name=self.name,
			caps=self.caps
		)

		self.log.debug('Launching Source-Distribution-Pipeline:\n%s', pipeline)
		self.distributionPipeline = Gst.parse_launch(pipeline)
		self.distributionPipeline.set_state(Gst.State.PLAYING)

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
		self.log.info("incomming connection from %s", addr)

		if self.currentConnection is not None:
			self.log.warn("another source is already connected")
			return True

		pipeline = """
			fdsrc fd={fd} !
			gdpdepay !
			{caps} !
			intervideosink channel={name}_in
		""".format(
			fd=conn.fileno(),
			name=self.name,
			caps=self.caps
		)
		self.log.debug('Launching Source-Receiver-Pipeline:\n%s', pipeline)
		self.receiverPipeline = Gst.parse_launch(pipeline)

		self.log.debug('Binding End-of-Stream-Signal on Source-Receiver-Pipeline')
		self.receiverPipeline.bus.add_signal_watch()
		self.receiverPipeline.bus.connect("message::eos", self.on_disconnect)

		self.receiverPipeline.set_state(Gst.State.PLAYING)

		self.currentConnection = conn
		return True

	def on_disconnect(self, bus, message):
		self.log.info('Received End-of-Stream-Signal on Source-Receiver-Pipeline')
		self.receiverPipeline.set_state(Gst.State.NULL)
		self.receiverPipeline = None

		self.currentConnection = None
