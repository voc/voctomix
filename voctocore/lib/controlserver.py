#!/usr/bin/python3
import socket, logging, traceback
from gi.repository import GObject

from lib.commands import ControlServerCommands
from lib.tcpmulticonnection import TCPMultiConnection

class ControlServer(TCPMultiConnection):
	log = logging.getLogger('ControlServer')

	boundSocket = None

	def __init__(self, pipeline):
		'''Initialize server and start listening.'''
		super().__init__(port=9999)

		self.commands = ControlServerCommands(pipeline)

	def on_accepted(self, conn, addr):
		'''Asynchronous connection listener. Starts a handler for each connection.'''

		self.log.debug('Setting GObject io-watch on Connection')
		GObject.io_add_watch(conn, GObject.IO_IN, self.on_data)

	def on_data(self, conn, *args):
		'''Asynchronous connection handler. Processes each line from the socket.'''
		# construct a file-like object fro mthe socket
		# to be able to read linewise and in utf-8
		filelike = conn.makefile('rw')

		# read a line from the socket
		line = ''
		try:
			line = filelike.readline().strip()
		except Exception as e:
			self.log.warn("Can't read from socket: %s", e)

		# no data = remote closed connection
		if len(line) == 0:
			self.close_connection(conn)
			return False

		# 'quit' = remote wants us to close the connection
		if line == 'quit':
			self.log.info("Client asked us to close the Connection")
			self.close_connection(conn)
			return False

		# process the received line
		success, msg = self.processLine(line)

		# success = False -> error 
		if success == False:
			# on error-responses the message is mandatory
			if msg is None:
				msg = '<no message>'

			# respond with 'error' and the message
			filelike.write('error '+msg+'\n')
			self.log.info("Function-Call returned an Error: %s", msg)

			# keep on listening on that connection
			return True

		# success = True and not message
		if msg is None:
			# respond with a simple 'ok'
			filelike.write('ok\n')
		else:
			# respond with the returned message
			filelike.write('ok '+msg+'\n')

		return True

	def processLine(self, line):
		# split line into command and optional args
		command, argstring = (line+' ').split(' ', 1)
		args = argstring.strip().split()

		# log function-call as parsed
		self.log.info("Read Function-Call from Socket: %s( %s )", command, args)

		# check that the function-call is a known Command
		if not hasattr(self.commands, command):
			return False, 'unknown command %s' % command


		try:
			# fetch the function-pointer
			f = getattr(self.commands, command)

			# call the function
			ret = f(*args)

			# if it returned an iterable, probably (Success, Message), pass that on
			if hasattr(ret, '__iter__'):
				return ret
			else:
				# otherwise construct a tuple
				return (ret, None)

		except Exception as e:
			self.log.error("Trapped Exception in Remote-Communication: %s", e)
			traceback.print_exc()

			# In case of an Exception, return that
			return False, str(e)
