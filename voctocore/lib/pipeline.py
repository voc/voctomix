import logging
from configparser import NoOptionError

# import library components
from lib.config import Config
from lib.sources import spawn_source
from lib.avrawoutput import AVRawOutput
from lib.avpreviewoutput import AVPreviewOutput
from lib.videomix import VideoMix
from lib.audiomix import AudioMix
from lib.streamblanker import StreamBlanker


class Pipeline(object):
    """mixing, streaming and encoding pipeline constuction and control"""

    def __init__(self):
        self.log = logging.getLogger('Pipeline')
        self.log.info('Video-Caps configured to: %s',
                      Config.get('mix', 'videocaps'))
        self.log.info('Audio-Caps configured to: %s',
                      Config.get('mix', 'audiocaps'))

        names = Config.getlist('mix', 'sources')
        if len(names) < 1:
            raise RuntimeError("At least one AVSource must be configured!")

        self.sources = []
        self.mirrors = []
        self.previews = []
        self.sbsources = []

        self.log.info('Creating %u AVSources: %s', len(names), names)
        for idx, name in enumerate(names):
            port = 10000 + idx

            outputs = [name + '_mixer']
            if Config.getboolean('previews', 'enabled'):
                outputs.append(name + '_preview')
            if Config.getboolean('mirrors', 'enabled'):
                outputs.append(name + '_mirror')

            source = spawn_source(name, port, outputs=outputs)
            self.log.info('Creating AVSource %s as %s', name, source)
            self.sources.append(source)

            if Config.getboolean('mirrors', 'enabled'):
                port = 13000 + idx
                self.log.info('Creating Mirror-Output for AVSource %s '
                              'at tcp-port %u', name, port)

                mirror = AVRawOutput('%s_mirror' % name, port)
                self.mirrors.append(mirror)

            if Config.getboolean('previews', 'enabled'):
                port = 14000 + idx
                self.log.info('Creating Preview-Output for AVSource %s '
                              'at tcp-port %u', name, port)

                preview = AVPreviewOutput('%s_preview' % name, port)
                self.previews.append(preview)

        self.log.info('Creating Videmixer')
        self.vmix = VideoMix()

        # check if there is an audio source preconfigured
        try:
            audiosource = Config.get('mix', 'audiosource')
            volumes = [0.0] * len(names)
            for source in audiosource.split(','):
                src, *volume = source.split(':', 1)
                volume = float(volume[0]) if volume else 1.0
                try:
                    volumes[names.index(src)] = volume
                except ValueError:
                    self.log.warn('Audiosource "%s" does not exist', src)
        except NoOptionError:
            volumes = []

        self.log.info('Creating Audiomixer')
        self.amix = AudioMix(volumes)

        port = 16000
        self.bgsrc = spawn_source('background', port, has_audio=False)
        self.log.info('Creating Mixer-Background VSource as %s', self.bgsrc)

        port = 11000
        self.log.info('Creating Mixer-Output at tcp-port %u', port)
        self.mixout = AVRawOutput('mix_out', port)

        if Config.getboolean('previews', 'enabled'):
            port = 12000
            self.log.info('Creating Preview-Output for AVSource %s '
                          'at tcp-port %u', name, port)

            self.mixpreview = AVPreviewOutput('mix_preview', port)

        if Config.getboolean('stream-blanker', 'enabled'):
            names = Config.getlist('stream-blanker', 'sources')
            if len(names) < 1:
                raise RuntimeError('At least one StreamBlanker-Source must '
                                   'be configured or the '
                                   'StreamBlanker disabled!')
            for idx, name in enumerate(names):
                port = 17000 + idx

                source = spawn_source('{}_streamblanker'.format(name), port,
                                      has_audio=False)
                self.log.info('Creating StreamBlanker VSource %s as %s',
                              name, source)
                self.sbsources.append(source)

            port = 18000
            self.log.info('Creating StreamBlanker ASource at tcp-port %u',
                          port)

            source = spawn_source('streamblanker', port, has_video=False)
            self.sbsources.append(source)

            self.log.info('Creating StreamBlanker')
            self.streamblanker = StreamBlanker()

            port = 15000
            self.log.info('Creating StreamBlanker-Output at tcp-port %u', port)
            self.streamout = AVRawOutput('streamblanker_out', port)
