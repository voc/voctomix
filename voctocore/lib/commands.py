#!/usr/bin/env python3
import logging
import json
import inspect

from voctocore.lib.config import Config
from voctocore.lib.response import NotifyResponse, OkResponse
from vocto.composite_commands import CompositeCommand
from vocto.command_helpers import quote, dequote, str2bool
import os

class ControlServerCommands(object):

    def __init__(self, pipeline):
        self.log = logging.getLogger('ControlServerCommands')

        self.pipeline = pipeline
        self.stored_values = {}

        self.sources = Config.getSources()
        self.blinder_sources = Config.getBlinderSources()
        self.streams = Config.getAudioStreams().get_stream_names()

    # Commands are defined below. Errors are sent to the clients by throwing
    # exceptions, they will be turned into messages outside.

    def message(self, *args):
        """sends a message through the control-server, which can be received by
        user-defined scripts. does not change the state of the voctocore."""
        return NotifyResponse('message', *args)

    def store_value(self, key, *args):
        """stores a value from a user-defined script in voctomix' memory.
        setting a value triggers a 'value'-broadcast.
        the value can be later retrieved using fetch_value.
        does not change the state of the voctocore."""
        value = ' '.join(args)
        self.stored_values[key] = value
        return NotifyResponse('value', key, value)

    def fetch_value(self, key):
        """retrieves a previusly stored value from a user-defined script.
        does not change the state of the voctocore."""
        try:
            value = self.stored_values[key]
        except KeyError:
            value = ""

        return OkResponse('value', key, value)

    def help(self):
        """displays help-messages for all commands"""
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
        helplines.append("Source-Names:")
        for source in self.sources:
            helplines.append("\t" + source)

        if Config.getBlinderEnabled():
            helplines.append("\n")
            helplines.append("Stream-Blanker Sources-Names:")
            for source in self.blinder_sources:
                helplines.append("\t" + source)

        return OkResponse("\n".join(helplines))

    def _get_video_status(self):
        a = self.pipeline.vmix.getVideoSourceA()
        b = self.pipeline.vmix.getVideoSourceB()
        return [a, b]

    def get_video(self):
        """gets the current video-status, consisting of the name of
           video-source A and video-source B"""
        status = self.pipeline.vmix.getVideoSources()
        return OkResponse('video_status', *status)

    def set_video_a(self, src_name):
        """sets the video-source A to the supplied source-name or source-id,
           swapping A and B if the supplied source is currently used as
           video-source B"""
        self.pipeline.vmix.setVideoSourceA(src_name)

        status = self.pipeline.vmix.getVideoSources()
        return NotifyResponse('video_status', *status)

    def set_video_b(self, src_name):
        """sets the video-source B to the supplied source-name or source-id,
           swapping A and B if the supplied source is currently used as
           video-source A"""
        self.pipeline.vmix.setVideoSourceB(src_name)

        status = self.pipeline.vmix.getVideoSources()
        return NotifyResponse('video_status', *status)

    def _get_audio_status(self):
        volumes = self.pipeline.amix.getAudioVolumes()

        return json.dumps({
            self.streams[idx]: round(volume, 4)
            for idx, volume in enumerate(volumes)
        })

    def get_audio(self):
        """gets the current volumes of the audio-sources"""
        status = self._get_audio_status()
        return OkResponse('audio_status', status)

    def set_audio(self, src_name):
        """sets the audio-source to the supplied source-name or source-id"""
        src_id = self.sources.index(src_name)
        self.pipeline.amix.setAudioSource(src_id)

        status = self._get_audio_status()
        return NotifyResponse('audio_status', status)

    def set_audio_volume(self, stream_name, volume):
        """sets the volume of the supplied source-name or source-id"""
        volume = float(volume)
        if volume < 0.0:
            raise ValueError("volume must be positive")
        if stream_name == 'mix':
            self.pipeline.amix.setAudioVolume(volume)
        else:
            self.pipeline.amix.setAudioSourceVolume(self.streams.index(stream_name), volume)

        status = self._get_audio_status()
        return NotifyResponse('audio_status', status)

    def get_composite_mode(self):
        """gets the name of the current composite-mode"""
        status = self.pipeline.vmix.getCompositeMode()
        return OkResponse('composite_mode', status)

    def get_composite_modes(self):
        """lists the names of all available composite-mode"""
        # TODO: fix this...
        #names = [mode.name for mode in CompositeModes]
        names = [""]
        namestr = ','.join(names)
        return OkResponse('composite_modes', namestr)

    def get_composite_mode_and_video_status(self):
        """retrieves the composite-mode and the video-status
        in a single call"""
        composite_status = self.pipeline.vmix.getCompositeMode()
        video_status = self.pipeline.vmix.getVideoSources()
        return OkResponse('composite_mode_and_video_status',
                          composite_status, *video_status)

    def set_composite_mode(self, mode_name):
        """sets the name of the id of the composite-mode"""
        self.pipeline.vmix.setComposite(CompositeCommand(mode_name, "*", "*"))

        composite_status = self.pipeline.vmix.getCompositeMode()
        video_status = self.pipeline.vmix.getVideoSources()
        return [
            NotifyResponse('composite_mode', composite_status),
            NotifyResponse('video_status', *video_status),
            NotifyResponse('composite_mode_and_video_status',
                           composite_status, *video_status),
        ]

    def transition(self, command):
        """sets the composite and sources by using the composite command format
           (e.g. 'sbs(cam1,cam2)') as the only parameter
        """
        self.pipeline.vmix.setComposite(command, True)
        return NotifyResponse('composite', self.pipeline.vmix.getComposite())

    def best(self, command):
        """tests if transition to the composite described by command is possible.
        """
        transition = self.pipeline.vmix.testTransition(command)
        if transition:
            return OkResponse('best','transition', *transition)
        else:
            cut = self.pipeline.vmix.testCut(command)
            if cut:
                return OkResponse('best','cut', *cut)
            else:
                command = CompositeCommand.from_str(command)
                return OkResponse('best','none',command.A,command.B)

    def cut(self, command):
        """sets the composite and sources by using the composite command format
           (e.g. 'sbs(cam1,cam2)') as the only parameter
        """
        self.pipeline.vmix.setComposite(command, False)
        return NotifyResponse('composite', self.pipeline.vmix.getComposite())

    def get_composite(self):
        """fetch current composite and sources using the composite command format
           (e.g. 'sbs(cam1,cam2)') as return value
        """
        return OkResponse('composite', self.pipeline.vmix.getComposite())

    def set_videos_and_composite(self, src_a_name, src_b_name,
                                 mode_name):
        """sets the A- and the B-source synchronously with the composition-mode
           all parametets can be set to "*" which will leave them unchanged."""
        self.pipeline.vmix.setComposite(
            str(CompositeCommand(mode_name, src_a_name, src_b_name)))

        composite_status = self.pipeline.vmix.getCompositeMode()
        video_status = self.pipeline.vmix.getVideoSources()

        return [
            NotifyResponse('composite_mode', composite_status),
            NotifyResponse('video_status', *video_status),
            NotifyResponse('composite_mode_and_video_status',
                           composite_status, *video_status),
        ]

    if Config.getBlinderEnabled():
        def _get_stream_status(self):
            blind_source = self.pipeline.blinder.blind_source
            if blind_source is None:
                return ('live',)

            return 'blinded', self.blinder_sources[blind_source]

        def get_stream_status(self):
            """gets the current blinder-status"""
            status = self._get_stream_status()
            return OkResponse('stream_status', *status)

        def set_stream_blind(self, source_name):
            """sets the blinder-status to blinder with the specified
               blinder-source-name or -id"""
            src_id = self.blinder_sources.index(source_name)
            self.pipeline.blinder.setBlindSource(src_id)

            status = self._get_stream_status()
            return NotifyResponse('stream_status', *status)

        # for backwards compatibility this command remains obsolete
        def set_stream_blank(self, source_name):

            return self.set_stream_blind(source_name)

        def set_stream_live(self):
            """sets the blinder-status to live"""
            self.pipeline.blinder.setBlindSource(None)

            status = self._get_stream_status()
            return NotifyResponse('stream_status', *status)

    def get_config(self):
        """returns the parsed server-config"""
        confdict = {header: dict(section)
                    for header, section in dict(Config).items()}
        return OkResponse('server_config', json.dumps(confdict))

    def get_config_option(self, section, key):
        """returns a single value from the server-config"""
        value = Config.get(section, key)
        return OkResponse('server_config_option', section, key, value)

    def report_queues(self):
        report = dict()
        for queue in self.pipeline.queues:
            report[queue.name] = queue.get_property("current-level-time")
        return OkResponse('queue_report', json.dumps(report))

    def report_ports(self):
        for p in self.pipeline.ports:
            p.update()
        return OkResponse('port_report', json.dumps(self.pipeline.ports, default=lambda x: x.todict()))

    # only available when overlays are configured
    if Config.hasOverlay():

        def set_overlay(self, overlay):
            """set an overlay and show"""
            # decode parameter to filename
            filename = Config.getOverlayFilePath(dequote(overlay))
            # check if file exists
            if os.path.isfile(filename):
                # select overlay in mixing pipeline
                self.pipeline.vmix.setOverlay(filename)
            else:
                # tell log about file that could not be found
                self.log.error(
                    "Overlay file '{}' not found".format(filename))
            # respond with current overlay notification
            return self.get_overlay()

        def show_overlay(self, visible):
            """set an overlay and show"""
            # show or hide overlay in mixing pipeline
            self.pipeline.vmix.showOverlay(str2bool(visible))
            # respond with overlay visibility notification
            return self.get_overlay_visible()

        def get_overlay(self):
            """respond any visible overlay"""
            return NotifyResponse('overlay', quote(Config.getOverlayNameFromFilePath(self.pipeline.vmix.getOverlay())))

        def get_overlay_visible(self):
            """respond any visible overlay"""
            return NotifyResponse('overlay_visible', str(self.pipeline.vmix.getOverlayVisible()))

        def get_overlays_title(self):
            """respond with list of all available overlays"""
            return NotifyResponse('overlays_title',
                                  ",".join(quote(t) for t in Config.getOverlaysTitle()))

        def get_overlays(self):
            return NotifyResponse('overlays',
                                  ",".join([quote(a) for a in Config.getOverlayFiles()]))
