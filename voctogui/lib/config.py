#!/usr/bin/python3
import logging
import os.path
from configparser import SafeConfigParser
from lib.args import Args
import lib.connection as Connection

__all__ = ['Config']

def getlist(self, section, option):
	return [x.strip() for x in self.get(section, option).split(',')]

def fetchRemoteConfig(self):
	log = logging.getLogger('Config')
	log.info("reading server-config %s", Connection)
	Connection.ask('config')

SafeConfigParser.getlist = getlist
SafeConfigParser.fetchRemoteConfig = fetchRemoteConfig

files = [
	os.path.join(os.path.dirname(os.path.realpath(__file__)), '../default-config.ini'),
	os.path.join(os.path.dirname(os.path.realpath(__file__)), '../config.ini'),
	'/etc/voctogui.ini',
	os.path.expanduser('~/.voctogui.ini'),
]

if Args.ini_file is not None:
	files.append(Args.ini_file)

Config = SafeConfigParser()
Config.read(files)
