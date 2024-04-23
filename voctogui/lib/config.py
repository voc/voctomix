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

    def getPresetComposites(self):
        return self.get('preset', 'composites', fallback=self.getToolbarComposites().get("buttons", "")).split(",")

    def getPresetSourcesComposites(self):
        return self._filterPresetSources(self.get('preset', 'sources_composites', fallback="").split(","))

    def getPresetSourcesFullscreen(self):
        return self._filterPresetSources(self.get('preset', 'sources_fullscreen', fallback="").split(","))

    def _filterPresetSources(self, sources):
        toolbar_sources = self.getToolbarSourcesA().get("buttons", "").split(",")
        sources = [source for source in sources if source]
        if not sources:
            return toolbar_sources
        else:
            filtered_sources = []
            for source in sources:
                if source in toolbar_sources:
                    filtered_sources.append(source)
            return filtered_sources

    def getShowCloseButton(self):
        return self.getboolean('toolbar', 'close', fallback=True)

    def getShowFullScreenButton(self):
        return self.getboolean('toolbar', 'fullscreen', fallback=False)

    def getShowQueueButton(self):
        return self.getboolean('toolbar', 'queues', fallback=False)

    def getShowPortButton(self):
        return self.getboolean('toolbar', 'ports', fallback=True)

    def getToolbarSourcesDefault(self):
        return {"%s.name" % source:
                source.upper()
                for source in self.getVideoSources()
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

    Config = VoctoguiConfigParser()

    config_file_name = Args.ini_file if Args.ini_file else os.path.join(
        os.path.dirname(os.path.realpath(__file__)), '../default-config.ini')
    readfiles = Config.read([config_file_name])

    log.debug("successfully parsed config-file: '%s'", config_file_name)

    if Args.ini_file is not None and Args.ini_file not in readfiles:
        raise RuntimeError('explicitly requested config-file "{}" '
                           'could not be read'.format(Args.ini_file))
