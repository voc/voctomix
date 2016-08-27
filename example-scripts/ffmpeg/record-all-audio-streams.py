#!/usr/bin/env python3
import socket
import sys
import json
import shlex
import subprocess
import logging
from configparser import SafeConfigParser

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('record-all-audio-streams')

host = 'localhost'
port = 9999

log.info('Connecting to %s:%u', host, port)
conn = socket.create_connection( (host, port) )
fd = conn.makefile('rw')

log.info('Fetching Config from Server')
fd.write("get_config\n");
fd.flush()
for line in fd:
	if line.startswith('server_config'):
		words = line.split(' ')
		args = words[1:]
		server_config_json = " ".join(args)
		log.info('Received Config from Server')
		break

log.info('Parsing Server-Config')
server_config = json.loads(server_config_json)

def getlist(self, section, option):
	return [x.strip() for x in self.get(section, option).split(',')]

SafeConfigParser.getlist = getlist


config = SafeConfigParser()
config.read_dict(server_config)

sources = config.getlist('mix', 'sources')

inputs = []
maps = []
for idx, source in enumerate(sources):
	inputs.append('-i tcp://localhost:%u' % (13000+idx))
	maps.append('-map %u:a -metadata:s:a:%u language=und' % (idx, idx))

try:
	output = sys.argv[1]
except:
	output = 'output.ts'

cmd = """
ffmpeg \
	-hide_banner
	-y -nostdin
	%s
	-ac 2 -channel_layout stereo
	%s
	-c:a mp2 -b:a 192k -ac:a 2 -ar:a 48000
	-flags +global_header -flags +ilme+ildct
	-f mpegts
	%s
""" % (' '.join(inputs), ' '.join(maps), output)
log.info('running command:\n%s', cmd)
args = shlex.split(cmd)
p = subprocess.run(args)
sys.exit(p.returncode)
