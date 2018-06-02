import logging
from gi.repository import Gtk, Gdk

from lib.config import Config
from lib.uibuilder import UiBuilder

from lib.videodisplay import VideoDisplay
from lib.audioleveldisplay import AudioLevelDisplay
from lib.warningoverlay import VideoWarningOverlay

from lib.videopreviews import VideoPreviewsController

from lib.toolbar.composition import CompositionToolbarController
from lib.toolbar.streamblank import StreamblankToolbarController
from lib.toolbar.misc import MiscToolbarController

from lib.shortcuts import show_shortcuts

from lib.studioclock import StudioClock


class Ui(UiBuilder):

    def __init__(self, uifile):
        self.log = logging.getLogger('Ui')
        super().__init__(uifile)

    def setup(self):
        self.log.info('Initializing Ui')

        # Aquire the Main-Window from the UI-File
        self.win = self.get_check_widget('window')

        # check for configuration option mainwindow/force_fullscreen
        if Config.getboolean('mainwindow', 'forcefullscreen', fallback=False):
            self.log.info(
                'Forcing main window to full screen by configuration')
            # set window into fullscreen mode
            self.win.fullscreen()
        else:
            # check for configuration option mainwindow/width and /height
            if Config.has_option('mainwindow', 'width') \
                    and Config.has_option('mainwindow', 'height'):
                # get size from config
                width = Config.getint('mainwindow', 'width')
                height = Config.getint('mainwindow', 'height')
                self.log.info(
                    'Set window size by configuration to %d:%d', width, height)
                # set window size
                self.win.set_size_request(width, height)
                self.win.set_resizable(False)

        # Connect Close-Handler
        self.win.connect('delete-event', Gtk.main_quit)

        # Get Audio-Level Display
        self.audio_level_display = self.find_widget_recursive(
            self.win, 'audiolevel_main')
        # Create Main-Video Overlay Controller
        drawing_area = self.find_widget_recursive(self.win,
                                                  'video_overlay_drawingarea')
        self.video_warning_overlay = VideoWarningOverlay(drawing_area)

        # Create Main-Video Display
        drawing_area = self.find_widget_recursive(self.win, 'video_main')
        self.main_video_display = VideoDisplay(
            drawing_area,
            port=11000,
            play_audio=Config.getboolean('mainvideo', 'playaudio'),
            level_callback=self.audio_level_display.level_callback
        )

        # Setup Preview Controller
        box_left = self.find_widget_recursive(self.win, 'box_left')
        self.video_previews_controller = VideoPreviewsController(
            box_left,
            win=self.win,
            uibuilder=self
        )

        # Setup Toolbar Controllers
        toolbar = self.find_widget_recursive(self.win, 'toolbar')
        self.composition_toolbar_controller = CompositionToolbarController(
            toolbar,
            win=self.win,
            uibuilder=self
        )

        self.streamblank_toolbar_controller = StreamblankToolbarController(
            toolbar,
            win=self.win,
            uibuilder=self,
            warning_overlay=self.video_warning_overlay
        )

        self.misc_controller = MiscToolbarController(
            toolbar,
            win=self.win,
            uibuilder=self
        )

        # Setup Shortcuts window
        self.win.connect('key-press-event', self.handle_keypress)
        self.win.connect('window-state-event', self.handle_state)

    def handle_keypress(self, window, event):
        if event.keyval == Gdk.KEY_question:
            show_shortcuts(window)

    def handle_state(self, window, event):
        # force full screen if whished by configuration
        if Config.getboolean('mainwindow', 'forcefullscreen', fallback=False):
            self.log.info('re-forcing fullscreen mode')
            self.win.fullscreen()

    def show(self):
        self.log.info('Showing Main-Window')
        self.win.show_all()
