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

def ask(command):
	print("would send command talk to server now and read back the response")
