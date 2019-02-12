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
    def __getList(self, section, option):
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

    def getHost(self):
        return Args.host if Args.host else self.get('server', 'host')

    def getSources(self):
        return self.__getList('mix', 'sources')

    def getVideoCaps(self, section='mix'):
        return self.get(section, 'videocaps')

    def getAudioCaps(self, section='mix'):
        return self.get(section, 'audiocaps')

    def getVideoSize(self, section='mix'):
        caps = Gst.Caps.from_string(
            self.getVideoCaps(section)).get_structure(0)
        _, width = caps.get_int('width')
        _, height = caps.get_int('height')
        return (width, height)

    def getFramerate(self, section='mix'):
        caps = Gst.Caps.from_string(
            self.getVideoCaps(section)).get_structure(0)
        (_, numerator, denominator) = caps.get_fraction('framerate')
        return (numerator, denominator)

    def getVideoSystem(self):
        return self.get('videodisplay', 'system', fallback='gl')

    def getPlayAudio(self):
        return self.getboolean('audio', 'play', fallback=True)

    def getVolumeControl(self):
        # Check if there is a fixed audio source configured.
        # If so, we will remove the volume sliders entirely
        # instead of setting them up.
        return (self.getboolean('audio', 'volumecontrol', fallback=True) or
                self.getboolean('audio', 'forcevolumecontrol', fallback=False))

    def getStreamBlankerEnabled(self):
        return self.getboolean('stream-blanker', 'enabled', fallback=False)

    def getStreamBlankerSources(self):
        return self.__getList('stream-blanker', 'sources')

    def getPreviewCaps(self):
        if self.has_option('previews', 'videocaps'):
            return self.getVideoCaps('previews')
        else:
            return self.getVideoCaps()

    def getPreviewSize(self):
        width = self.getint('previews', 'width') if self.has_option(
            'previews', 'width') else 320
        height = self.getint('previews', 'height') if self.has_option(
            'previews', 'height') else int(width * 9 / 16)
        return(width, height)

    def getUsePreviews(self):
        # @TODO: why double boolean?
        return self.getboolean('previews', 'enabled') \
            and self.getboolean('previews', 'use')

    def getPreviewDecoder(self):
        if self.has_option('previews', 'vaapi'):
            return self.get('previews', 'vaapi')
        else:
            return 'jpeg'

    def getComposites(self):
        return Composites.configure(self.items('composites'), self.getVideoSize())

    def getTargetComposites(self):
        return Composites.targets(self.getComposites())

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

    def getToolbarSourcesDefault(self):
        return {"%s.name" % source:
                source.upper()
                for source in self.__getList('mix', 'sources')
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
