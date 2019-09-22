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

    def getWindowSize(self):
        if self.has_option('mainwindow', 'width') \
                and self.has_option('mainwindow', 'height'):
            # get size from config
            return (self.getint('mainwindow', 'width'),
                    self.getint('mainwindow', 'height'))
        else:
            return None

    def getForceFullScreen(self):
        return self.getboolean('mainwindow', 'forcefullscreen', fallback=False)

    def getShowCloseButton(self):
        return self.getboolean('misc', 'close')

    def getShowFullScreenButton(self):
        return self.getboolean('misc', 'fullscreen')

    def getShowQueueButton(self):
        return self.getboolean('misc', 'debug')

    def getShowPortButton(self):
        return self.getboolean('misc', 'debug')

    def getShowShortcutButton(self):
        return self.getboolean('misc', 'shortcuts')

    def getToolbarSourcesDefault(self):
        return {"%s.name" % source:
                source.upper()
                for source in self.getList('mix', 'sources')
                }

    def trySection(self, section_name, default_result=None):
        return self[section_name] if self.has_section(section_name) else default_result

    def getToolbarSourcesA(self):
        return self.trySection('toolbar.sources.a', self.getToolbarSourcesDefault())

    def getToolbarSourcesB(self):
        return self.trySection('toolbar.sources.b', self.getToolbarSourcesDefault())

    def getToolbarCompositesDefault(self):
        return {"%s.name" % composite.name:
                composite.name.upper()
                for composite in self.getTargetComposites()
                }

    def getToolbarComposites(self):
        return self.trySection('toolbar.composites', self.getToolbarCompositesDefault())

    def getToolbarMods(self):
        return self.trySection('toolbar.mods', {})

    def getToolbarMixDefault(self):
        return {"retake.name": "RETAKE",
                "cut.name": "CUT",
                "trans.name": "TRANS"
                }

    def getToolbarMix(self):
        return self.trySection('toolbar.mix', self.getToolbarMixDefault())

    def getToolbarInsert(self):
        return self.trySection('toolbar.insert', {})

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
