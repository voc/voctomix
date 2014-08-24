import os.path
from configparser import SafeConfigParser

def getlist(self, section, option):
	return [x.strip() for x in self.get(section, option).split(',')]

SafeConfigParser.getlist = getlist

Config = SafeConfigParser()
Config.read([
	'default-config.ini',
	'/etc/voctomix.ini',
	os.path.expanduser('~/.voctomix.ini')
])
