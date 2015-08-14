#!/usr/bin/python3
import logging, socket
from gi.repository import GObject

from lib.config import Config

class TCPMultiConnection(object):
	def __init__(self, port):
		if not hasattr(self, 'log'):
			self.log = logging.getLogger('TCPMultiConnection')

		self.boundSocket = None
		self.currentConnections = []

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

		self.currentConnections.append(conn)
		self.log.info('Now %u Receiver connected', len(self.currentConnections))

		self.on_accepted(conn, addr)

		return True

	def close_connection(self, conn):
		self.currentConnections.remove(conn)
		self.log.info('Now %u Receiver connected', len(self.currentConnections))
