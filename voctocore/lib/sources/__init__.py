import logging

from lib.config import Config
from lib.sources.decklinkavsource import DeckLinkAVSource
from lib.sources.imgvsource import ImgVSource
from lib.sources.tcpavsource import TCPAVSource

log = logging.getLogger('AVSourceManager')

sources = {}


def spawn_source(name, port, outputs=None,
                 has_audio=True, has_video=True,
                 force_num_streams=None):

    section = 'source.{}'.format(name)
    kind = Config.get(section, 'kind', fallback='tcp')

    if kind == 'img':
        sources[name] = ImgVSource(name, outputs, has_audio, has_video)
        return sources[name]

    if kind == 'decklink':
        sources[name] = DeckLinkAVSource(name, outputs, has_audio, has_video)
        return sources[name]

    if kind != 'tcp':
        log.warning('Unknown source kind "%s", defaulting to "tcp"', kind)

    sources[name] = TCPAVSource(name, port, outputs,
                                has_audio, has_video,
                                force_num_streams)
    return sources[name]


def restart_source(name):
    sources[name].restart()
