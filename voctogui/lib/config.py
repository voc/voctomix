#!/usr/bin/env python3
import os.path
import logging
from lib.args import Args
import lib.connection as Connection
from vocto.config import VocConfigParser
__all__ = ['Config']

Config = None

log = logging.getLogger('VoctoguiConfigParser')

class VoctoguiConfigParser(VocConfigParser):

    def fetchServerConfig(self):
        log.info("reading server-config")

        server_config = Connection.fetchServerConfig()

        log.info("merging server-config %s", server_config)
        self.read_dict(server_config)

    def getHost(self):
        return Args.host if Args.host else self.get('server', 'host')

def load():
    global Config

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

    Config = VoctoguiConfigParser()
    readfiles = Config.read(files)

    log.debug('considered config-files: \n%s',
              "\n".join([
                  "\t\t" + os.path.normpath(file)
                  for file in files
              ]))
    log.debug('successfully parsed config-files: \n%s',
              "\n".join([
                  "\t\t" + os.path.normpath(file)
                  for file in readfiles
              ]))

    if Args.ini_file is not None and Args.ini_file not in readfiles:
        raise RuntimeError('explicitly requested config-file "{}" '
                           'could not be read'.format(Args.ini_file))
