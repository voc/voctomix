import socket, threading, queue, logging
from gi.repository import GObject

def controlServerEntrypoint(f):
	# mark the method as something that requires view's class
	f.is_control_server_entrypoint = True
	return f

class ControlServer():
	log = logging.getLogger('ControlServer')
	def __init__(self, videomix):
		'''Initialize server and start listening.'''
		self.videomix = videomix

		sock = socket.socket()
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		sock.bind(('0.0.0.0', 23000))
		sock.listen(1)

		# register socket for callback inside the GTK-Mainloop
		GObject.io_add_watch(sock, GObject.IO_IN, self.listener)

	def listener(self, sock, *args):
		'''Asynchronous connection listener. Starts a handler for each connection.'''
		conn, addr = sock.accept()
		self.log.info("Connection from %s", addr)

		# register data-received handler inside the GTK-Mainloop
		GObject.io_add_watch(conn, GObject.IO_IN, self.handler)
		return True

	def handler(self, conn, *args):
		'''Asynchronous connection handler. Processes each line from the socket.'''
		line = conn.recv(4096)
		if not len(line):
			self.log.debug("Connection closed.")
			return False

		r = self.processLine(line.decode('utf-8'))
		if isinstance(r, str):
			conn.send((r+'\n').encode('utf-8'))
			return False

		conn.send('OK\n'.encode('utf-8'))
		return True




	def processLine(self, line):
		command, argstring = (line.strip()+' ').split(' ', 1)
		args = argstring.strip().split()
		self.log.info(command % args)

		if not hasattr(self.videomix, command):
			return 'unknown command {}'.format(command)

		f = getattr(self.videomix, command)
		if not hasattr(f, 'is_control_server_entrypoint'):
			return 'method {} not callable from controlserver'.format(command)

		try:
			return f(*args)
		except Exception as e:
			return str(e)
