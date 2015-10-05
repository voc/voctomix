#!/usr/bin/python3
import socket, logging, traceback
from queue import Queue
from gi.repository import GObject

from lib.commands import ControlServerCommands
from lib.tcpmulticonnection import TCPMultiConnection
from lib.response import NotifyResponse, OkResponse

class ControlServer(TCPMultiConnection):
	def __init__(self, pipeline):
		'''Initialize server and start listening.'''
		self.log = logging.getLogger('ControlServer')
		super().__init__(port=9999)

		self.command_queue = Queue()

		self.commands = ControlServerCommands(pipeline)

		GObject.idle_add(self.on_loop)

	def on_accepted(self, conn, addr):
		'''Asynchronous connection listener. Starts a handler for each connection.'''
		self.log.debug('setting gobject io-watch on connection')
		GObject.io_add_watch(conn, GObject.IO_IN, self.on_data, [''])
		GObject.io_add_watch(conn, GObject.IO_OUT, self.on_write)

	def on_data(self, conn, _, leftovers, *args):
		'''Asynchronous connection handler. Pushes data from socket
		into command queue linewise'''
		close_after = False
		try:
			while True:
				try:
					leftovers.append(conn.recv(4096).decode(errors='replace'))
					if len(leftovers[-1]) == 0:
						self.log.info("Socket was closed")
						leftovers.pop()
						close_after = True
						break

				except UnicodeDecodeError as e:
					continue
		except BlockingIOError as e:
			pass

		data = "".join(leftovers)
		leftovers.clear()

		lines = data.split('\n')
		for line in lines[:-1]:
			self.log.debug("got line: %r", line)

			line = line.strip()
			# TODO: move quit to on_loop
			# 'quit' = remote wants us to close the connection
			if line == 'quit':
				self.log.info("Client asked us to close the Connection")
				self.close_connection(conn)
				return False

			self.command_queue.put((line, conn))

		if close_after:
			self.close_connection(conn)
			return False

		if lines[-1] != '':
			self.log.debug("remaining %r", lines[-1])

		leftovers.append(lines[-1])
		return True

	def on_loop(self):
		'''Command handler. Processes commands in the command queue whenever
		nothing else is happening (registered as GObject idle callback)'''
		if self.command_queue.empty():
			return True
		line, requestor = self.command_queue.get()

		words = line.split()
		if len(words) < 1:
			return True

		command = words[0]
		args = words[1:]

		self.log.info("processing command %r with args %s", command, args)

		try:
			command_function = self.commands.__class__.__dict__[command]

		except KeyError as e:
			self.log.info("received unknown command %s", command)
			response = "error unknown command %s\n" % command

		else:
			try:
				responseObject = command_function(self.commands, *args)

			except Exception as e:
				message = str(e) or "<no message>"
				response = "error %s\n" % message

			else:
				if isinstance(responseObject, NotifyResponse):
					signal = "%s\n" % str(responseObject)
					for conn, queue in self.currentConnections.items():
						if conn == requestor:
							continue

						queue.put(signal)

				response = "%s\n" % str(responseObject)

		finally:
			if requestor in self.currentConnections:
				self.currentConnections[requestor].put(response)

		return True

	def on_write(self, conn, *args):
		# TODO: on_loop() is not called as soon as there is a writable socket
		self.on_loop()

		try:
			queue = self.currentConnections[conn]
		except KeyError:
			return False

		if queue.empty():
			return True

		message = queue.get()
		try:
			conn.send(message.encode())
		except Exception as e:
			self.log.warn(e)

		return True

	def notify_all(self, msg):
		try:
			words = msg.split()
			words[-1] = self.commands.encodeSourceName(int(words[-1]))
			msg = " ".join(words) + '\n'
			for queue in self.currentConnections.values():
				queue.put(msg)
		except Exception as e:
			self.log.debug("error during notify: %s", e)
