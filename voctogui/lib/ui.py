import gi
import logging
from gi.repository import Gtk, Gst, Gdk, GLib

from lib.config import Config
from lib.uibuilder import UiBuilder

from lib.videodisplay import VideoDisplay
from lib.audioleveldisplay import AudioLevelDisplay
from lib.warningoverlay import VideoWarningOverlay

from lib.videopreviews import VideoPreviewsController
from lib.audioselector import AudioSelectorController

from lib.toolbar.composition import CompositionToolbarController
from lib.toolbar.streamblank import StreamblankToolbarController
from lib.toolbar.misc import MiscToolbarController


class Ui(UiBuilder):

    def __init__(self, uifile):
        self.log = logging.getLogger('Ui')
        super().__init__(uifile)

    def setup(self):
        self.log.info('Initializing Ui')

        # Aquire the Main-Window from the UI-File
        self.win = self.get_check_widget('window')

        # Connect Close-Handler
        self.win.connect('delete-event', Gtk.main_quit)

        # Create Audio-Level Display
        drawing_area = self.find_widget_recursive(self.win, 'audiolevel_main')
        self.audio_level_display = AudioLevelDisplay(drawing_area)

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
        drawing_area = self.find_widget_recursive(self.win, 'box_left')
        self.video_previews_controller = VideoPreviewsController(
            drawing_area,
            win=self.win,
            uibuilder=self
        )

        # check if there is a fixed audio source configured.
        # if so, remove the combo-box entirely instead of setting it up.
        if Config.has_option('mix', 'audiosource'):
            drawing_area.remove(self.find_widget_recursive(self.win, 'box_audio'))
        else:
            self.audio_selector_controller = AudioSelectorController(
                drawing_area=self.find_widget_recursive(self.win, 'combo_audio'),
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

    def show(self):
        self.log.info('Showing Main-Window')
        self.win.show_all()
