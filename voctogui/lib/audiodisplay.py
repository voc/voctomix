#!/usr/bin/env python3
import json
import logging
import math
import os
from configparser import NoOptionError

import lib.connection as Connection
from gi.repository import Gdk, GObject, Gtk
from lib.config import Config

from vocto.port import Port


class AudioDisplay(object):

    def __init__(self, audio_box, source, uibuilder, has_volume=True):
        self.log = logging.getLogger('VideoPreviewsController')
        self.source = source
        self.panel = None
        self.panels = dict()
        self.audio_streams = None
        self.volume_sliders = {}
        if source in Config.getSources():
            self.audio_streams = Config.getAudioStreams().get_source_streams(source)
            for name, stream in self.audio_streams.items():
                self.panels[name] = self.createAudioPanel(
                    name, audio_box, has_volume, uibuilder
                )
        else:
            self.panel = self.createAudioPanel(source, audio_box, has_volume, uibuilder)

    def createAudioPanel(self, name, audio_box, has_volume, uibuilder):
        audio = uibuilder.load_check_widget(
            'audio', os.path.dirname(uibuilder.uifile) + "/audio.ui"
        )
        audio_box.pack_start(audio, fill=False, expand=False, padding=0)
        audio_label = uibuilder.find_widget_recursive(audio, 'audio_label')
        audio_label.set_label(name.upper())

        self.init_volume_slider(name, audio, has_volume, uibuilder)

        return {"level": uibuilder.find_widget_recursive(audio, 'audio_level_display')}

    def callback(self, rms, peak, decay):
        if self.audio_streams:
            for name, streams in self.audio_streams.items():
                _rms = [0] * len(streams)
                _peak = [0] * len(streams)
                _decay = [0] * len(streams)
                for stream in streams:
                    _rms[stream.channel] = rms[stream.source_channel]
                    _peak[stream.channel] = peak[stream.source_channel]
                    _decay[stream.channel] = decay[stream.source_channel]
                self.panels[name]["level"].level_callback(_rms, _peak, _decay)
        elif self.panel:
            self.panel["level"].level_callback(rms, peak, decay)

    def init_volume_slider(self, name, audio_box, has_volume, uibuilder):
        volume_slider = uibuilder.find_widget_recursive(audio_box, 'audio_level')

        if has_volume:
            volume_signal = volume_slider.connect('value-changed', self.slider_changed)
            volume_slider.set_name(name)
            volume_slider.add_mark(-20.0, Gtk.PositionType.LEFT, "")
            volume_slider.add_mark(0.0, Gtk.PositionType.LEFT, "0")
            volume_slider.add_mark(10.0, Gtk.PositionType.LEFT, "")

            def slider_format(scale, value):
                if value == -20.0:
                    return "-\u221e\u202fdB"
                else:
                    return "{:.{}f}\u202fdB".format(value, scale.get_digits())

            volume_slider.connect('format-value', slider_format)
            self.volume_sliders[name] = (volume_slider, volume_signal)
            if not Config.getVolumeControl():
                volume_slider.set_sensitive(False)

            Connection.on('audio_status', self.on_audio_status)
            Connection.send('get_audio')
        else:
            volume_slider.set_no_show_all(True)
            volume_slider.hide()

    def slider_changed(self, slider):
        stream = slider.get_name()
        value = slider.get_value()
        volume = 10 ** (value / 20) if value > -20.0 else 0
        self.log.debug("slider_changed: {}: {:.4f}".format(stream, volume))
        Connection.send('set_audio_volume {} {:.4f}'.format(stream, volume))

    def on_audio_status(self, *volumes):
        volumes_json = "".join(volumes)
        volumes = json.loads(volumes_json)

        for stream, volume in volumes.items():
            if stream in self.volume_sliders:
                volume = 20.0 * math.log10(volume) if volume > 0 else -20.0
                slider, signal = self.volume_sliders[stream]
                # Temporarily block the 'value-changed' signal,
                # so we don't (re)trigger it when receiving (our) changes
                GObject.signal_handler_block(slider, signal)
                slider.set_value(volume)
                GObject.signal_handler_unblock(slider, signal)
