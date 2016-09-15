import logging
import json
import os.path
from configparser import SafeConfigParser
from lib.args import Args
import lib.connection as Connection

__all__ = ['Config']


def getlist(self, section, option):
    return [x.strip() for x in self.get(section, option).split(',')]


def fetchServerConfig(self):
    log = logging.getLogger('Config')
    log.info("reading server-config")

    server_config = Connection.fetchServerConfig()

    log.info("merging server-config %s", server_config)
    self.read_dict(server_config)

SafeConfigParser.getlist = getlist
SafeConfigParser.fetchServerConfig = fetchServerConfig

files = [
    os.path.join(os.path.dirname(os.path.realpath(__file__)),
                 '../default-config.ini'),
    os.path.join(os.path.dirname(os.path.realpath(__file__)),
                 '../config.ini'),
    '/etc/voctomix/voctogui.ini',
    '/etc/voctogui.ini',
    os.path.expanduser('~/.voctogui.ini'),
]

if Args.ini_file is not None:
    files.append(Args.ini_file)

Config = SafeConfigParser()
Config.read(files)
