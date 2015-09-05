#!/usr/bin/python3
import logging
import socket
import json
import sys
from queue import Queue
from gi.repository import GObject

log = logging.getLogger('Connection')
conn = None
port = 9999
command_queue = Queue()

def establish(host):
	global conn, port, log

	log.info('establishing Connection to %s', host)
	conn = socket.create_connection( (host, port) )
	log.debug('Connection successful \o/')

def fetchServerConfig():
	global conn, log

	log.info('reading server-config')
	fd = conn.makefile('rw')
	fd.write("get_config\n")
	fd.flush()

	while True:
		line = fd.readline()
		words = line.split(' ')

		signal = words[0]
		args = words[1:]

		if signal != 'server_config':
			continue

		server_config_json = " ".join(args)
		server_config = json.loads(server_config_json)
		return server_config


def enterNonblockingMode():
	global conn, log

	log.debug('entering nonblocking-mode')
	conn.setblocking(False)
	GObject.io_add_watch(conn, GObject.IO_IN, on_data, [''])
	GObject.idle_add(on_loop)

def on_data(conn, _, leftovers, *args):
	global log

	'''Asynchronous connection handler. Pushes data from socket
	into command queue linewise'''
	try:
		while True:
			try:
				leftovers.append(conn.recv(4096).decode(errors='replace'))
				if len(leftovers[-1]) == 0:
					log.info("socket was closed")

					# FIXME try to reconnect
					sys.exit(1)

			except UnicodeDecodeError as e:
				continue
	except BlockingIOError as e:
		pass

	data = "".join(leftovers)
	leftovers.clear()

	lines = data.split('\n')
	for line in lines[:-1]:
		log.debug("got line: %r", line)

		line = line.strip()
		command_queue.put((line, conn))

	log.debug("remaining %r", lines[-1])
	leftovers.append(lines[-1])
	return True

def on_loop():
	global command_queue

	'''Command handler. Processes commands in the command queue whenever
	nothing else is happening (registered as GObject idle callback)'''
	if command_queue.empty():
		return True

	line, requestor = command_queue.get()

	words = line.split()
	if len(words) < 1:
		return True

	signal = words[0]
	args = words[1:]

	log.info('received signal %s, dispatching', signal)

def send(command):
	global conn, log
	conn.send(command)

def on(signal, cb):
	pass

def one(signal, cb):
	pass
