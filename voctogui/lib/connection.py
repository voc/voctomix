#!/usr/bin/python3
import logging
import socket

log = logging.getLogger('Connection')
sock = None
port = 9999

def establish(host):
	log.info('establishing Connection to %s', host)
	sock = socket.create_connection( (host, port) )
	log.debug('Connection successful \o/')
	# TODO: register IO callback here


def send(command):
	print("would send command talk to server now and read back the response")
	filelike = sock.makefile('rw')
	filelike.write(command + "\n")
	filelike.flush()


def on_data(args*):
	filelike = sock.makefile()
	line = ''
	try:
		line = filelike.readline()
	except Exception as e:
		log.warn("Can't read from socket: %s", e)

	if len(line) == 0:
		close_connection()
		return False

	line = line.strip()

	process_line(line)


def process_line(line):
	msg_type = line.split()[0]


def close_connection():
	pass

