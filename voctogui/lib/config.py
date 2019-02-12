#!/usr/bin/env python3
import os.path
import logging
from gi.repository import Gst
from configparser import SafeConfigParser
from lib.args import Args
import lib.connection as Connection
from vocto.composites import Composites
__all__ = ['Config']

Config = None


class VocConfigParser(SafeConfigParser):
    def getlist(self, section, option):
        option = self.get(section, option).strip()
        if len(option) == 0:
            return []

        unfiltered = [x.strip() for x in option.split(',')]
        return list(filter(None, unfiltered))

    def fetchServerConfig(self):
        log = logging.getLogger('Config')
        log.info("reading server-config")

        server_config = Connection.fetchServerConfig()

        log.info("merging server-config %s", server_config)
        self.read_dict(server_config)

    def __trySection(self, section_name, default_result=None):
        return self[section_name] if self.has_section(section_name) else default_result

    def getVideoCaps(self, section='mix'):
        return Config.get(section, 'videocaps')

    def getVideoSize(self, section='mix'):
        caps = Gst.Caps.from_string(
            self.getVideoCaps(section)).get_structure(0)
        _, width = caps.get_int('width')
        _, height = caps.get_int('height')
        return (width, height)

    def getFramerate(self, section='mix'):
        caps = Gst.Caps.from_string(
            self.getVideoCaps(section)).get_structure(0)
        (_, framerate_numerator,
         framerate_denominator) = caps.get_fraction('framerate')
        return (framerate_numerator, framerate_denominator)

    def getComposites(self):
        return Composites.configure(self.items('composites'), self.getVideoSize())

    def getTargetComposites(self):
        return Composites.targets(self.getComposites())

    def getToolbarSourcesDefault(self):
        return {"%s.name" % source:
                source.upper()
                for source in Config.getlist('mix', 'sources')
                }

    def getToolbarSourcesA(self):
        return self.__trySection('toolbar.sources.a', self.getToolbarSourcesDefault())

    def getToolbarSourcesB(self):
        return self.__trySection('toolbar.sources.b', self.getToolbarSourcesDefault())

    def getToolbarCompositesDefault(self):
        return {"%s.name" % composite.name:
                composite.name.upper()
                for composite in self.getTargetComposites()
                }

    def getToolbarComposites(self):
        return self.__trySection('toolbar.composites', self.getToolbarCompositesDefault())

    def getToolbarMods(self):
        return self.__trySection('toolbar.mods', {})

    def getToolbarMixDefault(self):
        return {"retake.name": "RETAKE",
                "cut.name": "CUT",
                "trans.name": "TRANS"
                }

    def getToolbarMix(self):
        return self.__trySection('toolbar.mix', self.getToolbarMixDefault())


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

    Config = VocConfigParser()
    readfiles = Config.read(files)

    log = logging.getLogger('ConfigParser')
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
