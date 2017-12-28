import logging
import json
import inspect

from lib.config import Config
from lib.videomix import CompositeModes
from lib.response import NotifyResponse, OkResponse
from lib.sources import restart_source


class ControlServerCommands(object):
    def __init__(self, pipeline):
        self.log = logging.getLogger('ControlServerCommands')

        self.pipeline = pipeline

        self.sources = Config.getlist('mix', 'sources')
        self.audio_sources = []
        self.video_sources = []

        video_only = []
        audio_only = []

        try:
            audio_only = Config.getlist('mix', 'audio_only')
            video_only = Config.getlist('mix', 'video_only')
        except Exception:
            pass

        for source in self.sources:
            if source not in audio_only and source not in video_only:
                self.audio_sources.append(source)
                self.video_sources.append(source)
            elif source in video_only:
                self.video_sources.append(source)
            elif source in audio_only:
                self.audio_sources.append(source)

        if Config.getboolean('stream-blanker', 'enabled'):
            self.blankerSources = Config.getlist('stream-blanker', 'sources')

    # Commands are defined below. Errors are sent to the clients by throwing
    # exceptions, they will be turned into messages outside.

    def message(self, *args):
        """sends a message through the control-server, which can be received by
        user-defined scripts. does not change the state of the voctocore."""
        return NotifyResponse('message', *args)

    def help(self):
        helplines = []

        helplines.append("Commands:")
        for name, func in ControlServerCommands.__dict__.items():
            if name[0] == '_':
                continue

            if not func.__code__:
                continue

            params = inspect.signature(func).parameters
            params_iter = (str(info) for name, info in params.items())
            next(params_iter)
            params_str = ', '.join(params_iter)

            command_sig = '\t' + name

            if params_str:
                command_sig += ': ' + params_str

            if func.__doc__:
                command_sig += '\n\t\t{}\n'.format('\n\t\t'.join(
                    [line.strip() for line in func.__doc__.splitlines()]
                ))

            helplines.append(command_sig)

        helplines.append('\t' + 'quit / exit')

        helplines.append("\n")
        helplines.append("Video-Source Names:")
        for source in self.video_sources:
            helplines.append("\t" + source)

        helplines.append("Audio-Source Names:")
        for source in self.sources:
            helplines.append("\t" + source)

        if Config.getboolean('stream-blanker', 'enabled'):
            helplines.append("\n")
            helplines.append("Stream-Blanker Sources-Names:")
            for source in self.blankerSources:
                helplines.append("\t" + source)

        helplines.append("\n")
        helplines.append("Composition-Modes:")
        for mode in CompositeModes:
            helplines.append("\t" + mode.name)

        return OkResponse("\n".join(helplines))

    def _get_video_status(self):
        a = self.video_sources[self.pipeline.vmix.getVideoSourceA()]
        b = self.video_sources[self.pipeline.vmix.getVideoSourceB()]
        return [a, b]

    def get_video(self):
        """gets the current video-status, consisting of the name of
           video-source A and video-source B"""
        status = self._get_video_status()
        return OkResponse('video_status', *status)

    def set_video_a(self, src_name):
        """sets the video-source A to the supplied source-name or source-id,
           swapping A and B if the supplied source is currently used as
           video-source B"""
        src_id = self.video_sources.index(src_name)
        self.pipeline.vmix.setVideoSourceA(src_id)

        status = self._get_video_status()
        return NotifyResponse('video_status', *status)

    def set_video_b(self, src_name):
        """sets the video-source B to the supplied source-name or source-id,
           swapping A and B if the supplied source is currently used as
           video-source A"""
        src_id = self.video_sources.index(src_name)
        self.pipeline.vmix.setVideoSourceB(src_id)

        status = self._get_video_status()
        return NotifyResponse('video_status', *status)

    def _get_audio_status(self):
        volumes = self.pipeline.amix.getAudioVolumes()

        return json.dumps({
            self.audio_sources[idx]: round(volume, 4)
            for idx, volume in enumerate(volumes)
        })

    def get_audio(self):
        """gets the current volumes of the audio-sources"""
        status = self._get_audio_status()
        return OkResponse('audio_status', status)

    def set_audio(self, src_name):
        """sets the audio-source to the supplied source-name or source-id"""
        src_id = self.audio_sources.index(src_name)
        self.pipeline.amix.setAudioSource(src_id)

        status = self._get_audio_status()
        return NotifyResponse('audio_status', status)

    def set_audio_volume(self, src_name, volume):
        """sets the volume of the supplied source-name or source-id"""
        src_id = self.audio_sources.index(src_name)
        volume = float(volume)
        if volume < 0.0:
            raise ValueError("volume must be positive")
        self.pipeline.amix.setAudioSourceVolume(src_id, volume)

        status = self._get_audio_status()
        return NotifyResponse('audio_status', status)

    def _get_composite_status(self):
        mode = self.pipeline.vmix.getCompositeMode()
        return mode.name

    def get_composite_mode(self):
        """gets the name of the current composite-mode"""
        status = self._get_composite_status()
        return OkResponse('composite_mode', status)

    def get_composite_mode_and_video_status(self):
        composite_status = self._get_composite_status()
        video_status = self._get_video_status()
        return OkResponse('composite_mode_and_video_status',
                          composite_status, *video_status)

    def set_composite_mode(self, mode_name):
        """sets the name of the id of the composite-mode"""
        mode = CompositeModes[mode_name]
        self.pipeline.vmix.setCompositeMode(mode)

        composite_status = self._get_composite_status()
        video_status = self._get_video_status()
        return [
            NotifyResponse('composite_mode', composite_status),
            NotifyResponse('video_status', *video_status),
            NotifyResponse('composite_mode_and_video_status',
                           composite_status, *video_status),
        ]

    def set_videos_and_composite(self, src_a_name, src_b_name,
                                 mode_name):
        """sets the A- and the B-source synchronously with the composition-mode
           all parametets can be set to "*" which will leave them unchanged."""
        if src_a_name != '*':
            src_a_id = self.video_sources.index(src_a_name)
            self.pipeline.vmix.setVideoSourceA(src_a_id)

        if src_b_name != '*':
            src_b_id = self.video_sources.index(src_b_name)
            self.pipeline.vmix.setVideoSourceB(src_b_id)

        if mode_name != '*':
            mode = CompositeModes[mode_name]
            called_with_source = \
                src_a_name != '*' or \
                src_b_name != '*'

            self.pipeline.vmix.setCompositeMode(
                mode, apply_default_source=not called_with_source)

        composite_status = self._get_composite_status()
        video_status = self._get_video_status()

        return [
            NotifyResponse('composite_mode', composite_status),
            NotifyResponse('video_status', *video_status),
            NotifyResponse('composite_mode_and_video_status',
                           composite_status, *video_status),
        ]

    if Config.getboolean('stream-blanker', 'enabled'):
        def _get_stream_status(self):
            blankSource = self.pipeline.streamblanker.blankSource
            if blankSource is None:
                return ('live',)

            return 'blank', self.blankerSources[blankSource]

        def get_stream_status(self):
            """gets the current streamblanker-status"""
            status = self._get_stream_status()
            return OkResponse('stream_status', *status)

        def set_stream_blank(self, source_name):
            """sets the streamblanker-status to blank with the specified
               blanker-source-name or -id"""
            src_id = self.blankerSources.index(source_name)
            self.pipeline.streamblanker.setBlankSource(src_id)

            status = self._get_stream_status()
            return NotifyResponse('stream_status', *status)

        def set_stream_live(self):
            """sets the streamblanker-status to live"""
            self.pipeline.streamblanker.setBlankSource(None)

            status = self._get_stream_status()
            return NotifyResponse('stream_status', *status)

    def get_config(self):
        """returns the parsed server-config"""
        confdict = {header: dict(section)
                    for header, section in dict(Config).items()}
        return OkResponse('server_config', json.dumps(confdict))

    def restart_source(self, src_name):
        """restarts the specified source"""
        restart_source(src_name)
        return OkResponse('source_restarted', src_name)
