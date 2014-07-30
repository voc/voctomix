import socket, threading, queue
from gi.repository import GObject

class ControlServer():
	def __init__(self, videomix):
		'''Initialize server and start listening.'''
		self.videomix = videomix

		sock = socket.socket()
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		sock.bind(('0.0.0.0', 23000))
		sock.listen(1)
		GObject.io_add_watch(sock, GObject.IO_IN, self.listener)

	def listener(self, sock, *args):
		'''Asynchronous connection listener. Starts a handler for each connection.'''
		conn, addr = sock.accept()
		print("Connected")
		GObject.io_add_watch(conn, GObject.IO_IN, self.handler)
		return True

	def handler(self, conn, *args):
		'''Asynchronous connection handler. Processes each line from the socket.'''
		line = conn.recv(4096)
		if not len(line):
			print("Connection closed.")
			return False
		
		livevideo = self.videomix.pipeline.get_by_name('livevideo')
		pad = livevideo.get_static_pad('sink_1')
		pad.set_property('alpha', 00)
		print(line)
		return True
