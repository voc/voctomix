import logging
from gi.repository import Gtk, Gdk

from lib.config import Config
from lib.uibuilder import UiBuilder

from lib.videodisplay import VideoDisplay
from lib.audioleveldisplay import AudioLevelDisplay
from lib.audiodisplay import AudioDisplay
from lib.videopreviews import VideoPreviewsController
from lib.queues import QueuesWindowController
from lib.ports import PortsWindowController
from lib.presetcontroller import PresetController

from lib.toolbar.mix import MixToolbarController
from lib.toolbar.preview import PreviewToolbarController
from lib.toolbar.overlay import OverlayToolbarController
from lib.toolbar.blinder import BlinderToolbarController
from lib.toolbar.misc import MiscToolbarController

from lib.studioclock import StudioClock

from vocto.port import Port


class Ui(UiBuilder):

    def __init__(self, uifile):
        self.log = logging.getLogger('Ui')
        super().__init__(uifile)

    def setup(self):
        self.log.info('Initializing Ui')

        # Aquire the Main-Window from the UI-File
        self.win = self.get_check_widget('window')

        # check for configuration option mainwindow/force_fullscreen
        if Config.getForceFullScreen():
            self.log.info(
                'Forcing main window to full screen by configuration')
            # set window into fullscreen mode
            self.win.fullscreen()
        else:
            # check for configuration option mainwindow/width and /height
            if Config.getWindowSize():
                # set window size
                self.win.set_size_request(*Config.getWindowSize())
                self.win.set_resizable(False)

        # Connect Close-Handler
        self.win.connect('delete-event', Gtk.main_quit)

        output_aspect_ratio = self.find_widget_recursive(self.win, 'output_aspect_ratio')
        output_aspect_ratio_preview = self.find_widget_recursive(self.win, 'output_aspect_ratio_preview')
        output_aspect_ratio.props.ratio = Config.getVideoRatio()
        if Config.getPreviewMixEnabled():
            output_aspect_ratio_preview.props.hexpand = True
            output_aspect_ratio_preview.props.vexpand = True
            output_aspect_ratio_preview.set_visible(True)
            output_aspect_ratio_preview.props.ratio = Config.getVideoRatio()
        else:
            output_aspect_ratio_preview.props.hexpand = False
            output_aspect_ratio_preview.props.vexpand = False
            output_aspect_ratio_preview.set_visible(False)

        audio_box = self.find_widget_recursive(self.win, 'audio_box')

        # Setup Preview Controller
        self.video_previews = VideoPreviewsController(
            self.find_widget_recursive(self.win, 'preview_box'),
            audio_box,
            win=self.win,
            uibuilder=self
        )
        if Config.getPreviewsEnabled():
            for idx, source in enumerate(Config.getSources()):
                self.video_previews.addPreview(self, source,
                                               Port.SOURCES_PREVIEW + idx)
        elif Config.getMirrorsEnabled():
            for idx, source in enumerate(Config.getMirrorsSources()):
                self.video_previews.addPreview(
                    self, source, Port.SOURCES_OUT + idx)
        else:
            self.log.warning(
                'Can not show source previews because neither previews nor mirrors are enabled (see previews/enabled and mirrors/enabled in core configuration)')

        self.mix_audio_display = AudioDisplay(audio_box, "mix", uibuilder=self)

        # Create Main-Video Display
        self.mix_video_display = VideoDisplay(
            self.find_widget_recursive(self.win, 'video_main'),
            self.mix_audio_display,
            port=Port.MIX_PREVIEW if Config.getPreviewsEnabled() else Port.MIX_OUT,
            name="MIX"
        )
        self.premix_video_display = None
        if Config.getPreviewMixEnabled():
            self.premix_video_display = VideoDisplay(
                self.find_widget_recursive(self.win, 'video_main_preview'),
                None,
                port=Port.PREMIX_PREVIEW if Config.getPreviewsEnabled() else Port.PREMIX_OUT,
                name="PREMIX"
            )

        for idx, livepreview in enumerate(Config.getLivePreviews()):
            if Config.getPreviewsEnabled():
                self.video_previews.addPreview(
                    self, '{}-blinded'.format(livepreview), Port.LIVE_PREVIEW + idx, has_volume=False)
            else:
                self.video_previews.addPreview(
                    self, '{}-blinded'.format(livepreview), Port.LIVE_OUT + idx, has_volume=False)

        self.preview_toolbar_controller = PreviewToolbarController(
            win=self.win,
            uibuilder=self
        )

        self.preset_controller = PresetController(
            win=self.win,
            preview_controller=self.preview_toolbar_controller,
            uibuilder=self,
        )

        self.overlay_toolbar_controller = OverlayToolbarController(
            win=self.win,
            uibuilder=self
        )

        self.mix_toolbar_controller = MixToolbarController(
            win=self.win,
            uibuilder=self,
            preview_controller=self.preview_toolbar_controller,
            overlay_controller=self.overlay_toolbar_controller
        )

        self.blinder_toolbar_controller = BlinderToolbarController(
            win=self.win,
            uibuilder=self
        )

        self.queues_controller = QueuesWindowController(self)
        self.ports_controller = PortsWindowController(self)

        self.misc_controller = MiscToolbarController(
            win=self.win,
            uibuilder=self,
            queues_controller=self.queues_controller,
            ports_controller=self.ports_controller,
            video_display=self.mix_video_display
        )

        # Setup Shortcuts window
        self.win.connect('window-state-event', self.handle_state)

    def handle_state(self, window, event):
        # force full screen if whished by configuration
        if Config.getForceFullScreen():
            self.log.info('re-forcing fullscreen mode')
            self.win.fullscreen()

    def show(self):
        self.log.info('Showing Main-Window')
        self.win.show_all()
