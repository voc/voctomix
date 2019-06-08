import logging

from lib.config import Config
from lib.sources.decklinkavsource import DeckLinkAVSource
from lib.sources.imgvsource import ImgVSource
from lib.sources.tcpavsource import TCPAVSource
from lib.sources.testsource import TestSource
from lib.sources.videoloopsource import VideoLoopSource
from lib.sources.overlaysource import OverlaySource

log = logging.getLogger('AVSourceManager')

sources = {}


def spawn_source(name, port, has_audio=True, has_video=True,
                 force_num_streams=None):

    kind = Config.getSourceKind(name)

    if kind == 'img':
        sources[name] = ImgVSource(name)
    elif kind == 'decklink':
        sources[name] = DeckLinkAVSource(name, has_audio, has_video)
    elif kind == 'test':
        sources[name] = TestSource(name, has_audio, has_video)
    elif kind == 'videoloop':
        sources[name] = VideoLoopSource(name)
    elif kind == 'overlay':
        sources[name] = OverlaySource(name)
    elif kind == 'tcp':
        sources[name] = TCPAVSource(name, port, has_audio, has_video,
                                    force_num_streams)
    else:
        log.warning('Unknown source kind "%s", defaulting to "tcp"', kind)
    return sources[name]


def restart_source(name):
    assert False, "restart_source() not implemented"
