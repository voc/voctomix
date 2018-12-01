import logging
import json
import math
import os
from configparser import NoOptionError

from gi.repository import Gtk, GObject
from lib.videodisplay import VideoDisplay
import lib.connection as Connection

from lib.config import Config


class VideoPreviewsController(object):
    """Displays Video-Previews and selection Buttons for them"""

    def __init__(self, preview_box, win, uibuilder):
        self.log = logging.getLogger('VideoPreviewsController')

        self.preview_box = preview_box
        self.win = win

        self.sources = Config.getlist('mix', 'sources')
        self.preview_players = {}
        self.previews = {}
        self.volume_sliders = {}

        self.current_source = {'a': None, 'b': None}

        try:
            width = Config.getint('previews', 'width')
            self.log.debug('Preview-Width configured to %u', width)
        except NoOptionError:
            width = 320
            self.log.debug('Preview-Width selected as %u', width)

        try:
            height = Config.getint('previews', 'height')
            self.log.debug('Preview-Height configured to %u', height)
        except NoOptionError:
            height = int(width * 9 / 16)
            self.log.debug('Preview-Height calculated to %u', height)

        # Accelerators
        accelerators = Gtk.AccelGroup()
        win.add_accel_group(accelerators)

        # Check if there is a fixed audio source configured.
        # If so, we will remove the volume sliders entirely
        # instead of setting them up.
        volume_control = \
            Config.getboolean('audio', 'volumecontrol', fallback=True) or \
            Config.getboolean('audio', 'forcevolumecontrol', fallback=False)

        for idx, source in enumerate(self.sources):
            self.log.info('Initializing Video Preview %s', source)

            preview = uibuilder.load_check_widget(
                'widget_preview',
                os.path.dirname(uibuilder.uifile) + "/widgetpreview.ui")
            video = uibuilder.find_widget_recursive(preview, 'video')

            video.set_size_request(width, height)
            preview_box.pack_start(preview, fill=False,
                                   expand=False, padding=0)

            audio_level = uibuilder.find_widget_recursive(preview, 'audio_level_display')
            player = VideoDisplay(video, port=13000 + idx,
                                  width=width, height=height,
                                  level_callback=audio_level.level_callback
                                  )

            uibuilder.find_widget_recursive(preview, 'label').set_label(source)

            volume_slider = uibuilder.find_widget_recursive(preview,
                                                            'audio_level')

            if not volume_control:
                box = uibuilder.find_widget_recursive(preview, 'box')
                box.remove(volume_slider)
            else:
                volume_slider.set_name("volume {}".format(source))
                volume_signal = volume_slider.connect('value-changed',
                                                      self.slider_changed)
                volume_slider.add_mark(-20.0,Gtk.PositionType.LEFT,"")
                volume_slider.add_mark(0.0,Gtk.PositionType.LEFT,"0")
                volume_slider.add_mark(10.0,Gtk.PositionType.LEFT,"")

                def slider_format(scale, value):
                    if value == -20.0:
                        return "-\u221e\u202fdB"
                    else:
                        return "{:.{}f}\u202fdB".format(value,
                                                        scale.get_digits())

                volume_slider.connect('format-value', slider_format)
                self.volume_sliders[source] = (volume_slider, volume_signal)

            self.preview_players[source] = player
            self.previews[source] = preview
        # connect event-handler and request initial state
        Connection.on('video_status', self.on_video_status)
        Connection.send('get_video')

        if volume_control:
            Connection.on('audio_status', self.on_audio_status)
            Connection.send('get_audio')

    def btn_toggled(self, btn):
        if not btn.get_active():
            return

        btn_name = btn.get_name()
        self.log.debug('btn_toggled: %s', btn_name)

        channel, idx = btn_name.split(' ')[:2]
        source_name = self.sources[int(idx)]

        if self.current_source[channel] == source_name:
            self.log.info('video-channel %s already on %s',
                          channel, source_name)
            return

        self.log.info('video-channel %s changed to %s', channel, source_name)
        Connection.send('set_video_' + channel, source_name)

    def slider_changed(self, slider):
        slider_name = slider.get_name()
        source = slider_name.split(' ')[1]
        value = slider.get_value()
        volume = 10 ** (value / 20) if value > -20.0 else 0
        self.log.debug("slider_changed: {}: {:.4f}".format(source, volume))
        Connection.send('set_audio_volume {} {:.4f}'.format(source, volume))

    def on_video_status(self, source_a, source_b):
        self.log.info('on_video_status callback w/ sources: %s and %s',
                      source_a, source_b)

        self.current_source['a'] = source_a
        self.current_source['b'] = source_b

    def on_audio_status(self, *volumes):
        volumes_json = "".join(volumes)
        volumes = json.loads(volumes_json)

        for source, volume in volumes.items():
            volume = 20.0 * math.log10(volume) if volume > 0 else -20.0
            slider, signal = self.volume_sliders[source]
            # Temporarily block the 'value-changed' signal,
            # so we don't (re)trigger it when receiving (our) changes
            GObject.signal_handler_block(slider, signal)
            slider.set_value(volume)
            GObject.signal_handler_unblock(slider, signal)
