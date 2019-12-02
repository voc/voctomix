import logging

log = logging.getLogger('AVSourceManager')

sources = {}


def spawn_source(name, port, has_audio=True, has_video=True):

    from lib.config import Config
    from lib.sources.decklinkavsource import DeckLinkAVSource
    from lib.sources.imgvsource import ImgVSource
    from lib.sources.tcpavsource import TCPAVSource
    from lib.sources.testsource import TestSource
    from lib.sources.videoloopsource import VideoLoopSource

    from lib.config import Config
    from lib.sources.decklinkavsource import DeckLinkAVSource
    from lib.sources.imgvsource import ImgVSource
    from lib.sources.tcpavsource import TCPAVSource
    from lib.sources.testsource import TestSource
    from lib.sources.videoloopsource import VideoLoopSource
    from lib.sources.v4l2source import V4l2AVSource

    kind = Config.getSourceKind(name)

    if kind == 'img':
        sources[name] = ImgVSource(name)
    elif kind == 'decklink':
        sources[name] = DeckLinkAVSource(name, has_audio, has_video)
    elif kind == 'videoloop':
        sources[name] = VideoLoopSource(name)
    elif kind == 'tcp':
        sources[name] = TCPAVSource(name, port, has_audio, has_video)
    elif kind == 'v4l2':
        sources[name] = V4l2AVSource(name)
    else:
        if kind != 'test':
            log.warning(
                'Unknown value "%s" in attribute "kind" in definition of source %s (see section [source.%s] in configuration). Falling back to kind "test".', kind, name, name)
        sources[name] = TestSource(name, has_audio, has_video)

    return sources[name]


def kind_has_audio(source):
    return source in ["decklink", "tcp", "test"]


def restart_source(name):
    assert False, "restart_source() not implemented"
