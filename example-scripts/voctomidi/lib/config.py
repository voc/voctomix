import os.path
from configparser import SafeConfigParser

__all__ = ['Config']

modulepath = os.path.dirname(os.path.realpath(__file__))
files = [
    os.path.join(modulepath, '../default-config.ini'),
    os.path.join(modulepath, '../config.ini'),
    '/etc/voctomix/voctomidi.ini',
    '/etc/voctomidi.ini',
    os.path.expanduser('~/.voctomidi.ini'),
]

Config = SafeConfigParser()
Config.read(files)
