#!/usr/bin/env python3
import logging
import json
import math
import os
from configparser import NoOptionError

from gi.repository import Gtk, Gdk, GObject
from lib.videodisplay import VideoDisplay
from lib.audiodisplay import AudioDisplay
import lib.connection as Connection

from lib.config import Config
from vocto.port import Port


class VideoPreviewsController(object):
    """Displays Video-Previews and selection Buttons for them"""

    def __init__(self, video_box, audio_box, win, uibuilder):
        self.log = logging.getLogger('VideoPreviewsController')

        self.win = win

        self.preview_players = {}
        self.previews = {}
        self.volume_sliders = {}
        self.video_box = video_box
        self.audio_box = audio_box

        # Accelerators
        accelerators = Gtk.AccelGroup()
        win.add_accel_group(accelerators)

        # count number of previews
        num_previews = len(Config.getSources()) + len(Config.getLivePreviews())

        # get preview size
        self.previewSize = Config.getPreviewSize()

        # recalculate preview size if in sum they are too large for screen
        screen = Gdk.Screen.get_default()
        if screen.get_height() < self.previewSize[1] * num_previews:
            height = screen.get_height() / num_previews
            self.previewSize = (Config.getVideoRatio() * height, height)
            self.log.warning(
                'Resizing previews so that they fit onto screen to WxH={}x{}'.format(*self.previewSize))

        # connect event-handler and request initial state
        Connection.send('get_video')

    def addPreview(self, uibuilder, source, port, has_volume=True):

        self.log.info('Initializing video preview %s at port %d', source, port)

        mix_audio_display = None

        has_audio = source in Config.getAudioSources()
        if has_audio and Config.getAudioStreams().get_source_streams(source):
            mix_audio_display = AudioDisplay(self.audio_box, source, uibuilder, has_volume)
        if source in Config.getVideoSources(internal=True):
            video = uibuilder.load_check_widget('video',
                                                os.path.dirname(uibuilder.uifile) +
                                                "/widgetpreview.ui")
            video.set_size_request(*self.previewSize)
            self.video_box.pack_start(video, fill=False,
                                   expand=False, padding=0)

            player = VideoDisplay(video, mix_audio_display, port=port,
                                  width=self.previewSize[0],
                                  height=self.previewSize[1],
                                  name=source.upper(),
                                  has_audio=has_audio,
                                  )
