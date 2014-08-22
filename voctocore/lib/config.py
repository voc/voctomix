import os.path
from configparser import SafeConfigParser

Config = SafeConfigParser()
Config.read([
	'default-config.ini',
	'/etc/voctomix.ini',
	os.path.expanduser('~/.voctomix.ini')
])
