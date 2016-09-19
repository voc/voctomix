import logging

from lib.config import Config
from lib.sources.imgvsource import ImgVSource
from lib.sources.tcpavsource import TCPAVSource

log = logging.getLogger('AVSourceManager')

sources = {}


def spawn_source(name, port, outputs=None, has_audio=True, has_video=True):
    section = 'source.{}'.format(name)
    kind = Config.get(section, 'kind', fallback='tcp')

    if kind == 'img':
        sources[name] = ImgVSource(name, outputs, has_audio, has_video)
        return sources[name]

    if kind != 'tcp':
        log.warn('Unknown source kind "%s", defaulting to "tcp"', kind)

    sources[name] = TCPAVSource(name, port, outputs, has_audio, has_video)
    return sources[name]


def restart_source(name):
    sources[name].restart()
