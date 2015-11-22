#!/usr/bin/python3
import logging
from twisted.internet import protocol
from twisted.protocols.basic import LineOnlyReceiver

from lib.commands import ControlServerCommands
from lib.response import NotifyResponse, OkResponse


class ControlServerProtocol(LineOnlyReceiver):

	delimiter = b'\n'

	def connectionMade(self):
		self.commands = self.factory.commands
		self.log = self.factory.log
		self.factory.currentConnections.add(self)

	def connectionLost(self, reason=protocol.connectionDone):
		self.factory.currentConnections.remove(self)

	def reply(self, line):
		"""Send a reply to the client, encoded in UTF-8"""
		self.sendLine(line.encode('utf-8'))

	def lineReceived(self, line):
		# Decode to text
		line = line.decode(errors='replace')

		words = line.split()
		if len(words) < 1:
			return

		command = words[0]
		args = words[1:]

		self.log.info("processing command %r with args %s", command, args)

		if command == 'quit':
			self.transport.loseConnection()
			return

		response = None
		command_function = self.commands.__class__.__dict__.get(command)
		# deny calling private methods
		if command.startswith('_'):
			command_function = None

		if command_function is None:
			self.log.info("received unknown command %s", command)
			self.reply("error unknown command %s" % command)
			return

		try:
			responseObject = command_function(self.commands, *args)
		except Exception as e:
			message = str(e) or "<no message>"
			self.reply("error %s" % message)
			return

		if not isinstance(responseObject, list):
			responseObject = [responseObject]
		for obj in responseObject:
			if isinstance(obj, NotifyResponse):
				for p in self.factory.currentConnections:
					p.reply(str(obj))
			else:
				self.reply(str(obj))


class ControlServer(protocol.ServerFactory):

	protocol = ControlServerProtocol

	def __init__(self, pipeline):
		'''Initialize server and start listening.'''
		self.log = logging.getLogger('ControlServer')
		self.commands = ControlServerCommands(pipeline)
		self.currentConnections = set()

		# Delay importing reactor so we are sure gireactor has
		# been installed.
		from twisted.internet import reactor
		reactor.listenTCP(9999, self, interface="::")

