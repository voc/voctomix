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

    def __init__(self, preview_box, audio_box, win, uibuilder):
        self.log = logging.getLogger('VideoPreviewsController')

        self.win = win

        self.sources = Config.getSources()
        self.preview_players = {}
        self.previews = {}
        self.volume_sliders = {}

        # Accelerators
        accelerators = Gtk.AccelGroup()
        win.add_accel_group(accelerators)

        # count number of previews
        num_previews = len(self.sources)
        if Config.getLivePreviewEnabled():
            num_previews += 1

        # get preview size
        self.previewSize = Config.getPreviewSize()

        # recalculate preview size if in sum they are too large for screen
        screen = Gdk.Screen.get_default()
        if screen.get_height() < self.previewSize[1] * num_previews:
            height = screen.get_height() / num_previews
            self.previewSize = (Config.getVideoRatio() * height, height)
            self.log.warning(
                'Resizing previews so that they fit onto screen to WxH={}x{}'.format(*self.previewSize))

        if Config.getPreviewsEnabled():
            for idx, source in enumerate(self.sources):
                self.addPreview(uibuilder, preview_box, audio_box, source,
                                Port.SOURCES_PREVIEW + idx)
        elif Config.getMirrorsEnabled():
            for idx, source in enumerate(Config.getMirrorsSources()):
                self.addPreview(uibuilder, preview_box, audio_box,
                                source, Port.SOURCES_OUT + idx)
        else:
            self.log.warning(
                'Can not show source previews because neither previews nor mirrors are enabled (see previews/enabled and mirrors/enabled in core configuration)')

        if Config.getLivePreviewEnabled():
            if Config.getPreviewsEnabled():
                self.addPreview(uibuilder, preview_box, audio_box, "LIVE", Port.LIVE_PREVIEW)
            else:
                self.addPreview(uibuilder, preview_box, audio_box, "LIVE", Port.LIVE_OUT)

        # connect event-handler and request initial state
        Connection.send('get_video')

    def addPreview(self, uibuilder, preview_box, audio_box, source, port):

        self.log.info('Initializing video preview %s at port %d', source, port)

        video = uibuilder.load_check_widget('video',
                                            os.path.dirname(uibuilder.uifile) +
                                            "/widgetpreview.ui")
        video.set_size_request(*self.previewSize)
        preview_box.pack_start(video, fill=False,
                               expand=False, padding=0)

        mix_audio_display = AudioDisplay(audio_box, source, uibuilder)
        player = VideoDisplay(video, mix_audio_display, port=port,
                              width=self.previewSize[0],
                              height=self.previewSize[1],
                              name=source.upper()
                              )
