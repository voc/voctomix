import logging

log = logging.getLogger('AVSourceManager')

sources = {}


def spawn_source(name, port, has_audio=True, has_video=True):

    from lib.config import Config
    from lib.sources.alsaaudiosource import AlsaAudioSource
    from lib.sources.decklinkavsource import DeckLinkAVSource
    from lib.sources.filesource import FileSource
    from lib.sources.imgvsource import ImgVSource
    from lib.sources.pulseaudiosource import PulseAudioSource
    from lib.sources.rpicamsource import RPICamAVSource
    from lib.sources.tcpavsource import TCPAVSource
    from lib.sources.testsource import TestSource
    from lib.sources.v4l2source import V4l2AVSource

    kind = Config.getSourceKind(name)

    if kind == 'img':
        sources[name] = ImgVSource(name)
    elif kind == 'decklink':
        sources[name] = DeckLinkAVSource(name, has_audio, has_video)
    elif kind == 'file':
        sources[name] = FileSource(name, has_audio, has_video)
    elif kind == 'tcp':
        sources[name] = TCPAVSource(name, port, has_audio, has_video)
    elif kind == 'v4l2':
        sources[name] = V4l2AVSource(name)
    elif kind == 'RPICam':
        sources[name] = RPICamAVSource(name)
    elif kind == 'pa':
        sources[name] = PulseAudioSource(name)
    elif kind == 'alsa':
        sources[name] = AlsaAudioSource(name)
    else:
        if kind != 'test':
            log.warning(
                'Unknown value "%s" in attribute "kind" in definition of source %s (see section [source.%s] in configuration). Falling back to kind "test".',
                kind,
                name,
                name,
            )
        sources[name] = TestSource(name, has_audio, has_video)

    return sources[name]
