import logging
from typing import cast

from gi.repository import Gtk, Gdk, Adw

from voctogui2.lib.config import Config
from voctogui2.lib.studioclock import StudioClock

from voctogui2.lib.videodisplay import VideoDisplay
from voctogui2.lib.audiodisplay import AudioDisplay
from voctogui2.lib.videopreviews import VideoPreviewsController
from voctogui2.lib.queues import QueuesWindowController, VoctoguiQueueWindow
from voctogui2.lib.ports import PortsWindowController, VoctoguiPortsWindow
from voctogui2.lib.presetcontroller import PresetController, VoctoguiPresetToolbar

from voctogui2.lib.toolbar.mix import MixToolbarController
from voctogui2.lib.toolbar.preview import PreviewToolbarController, VoctoguiPreviewToolbar
from voctogui2.lib.toolbar.overlay import OverlayToolbarController, VoctoguiOverlayToolbar
from voctogui2.lib.toolbar.blinder import BlinderToolbarController, VoctoguiBlinderToolbar
from voctogui2.lib.toolbar.misc import MiscToolbarController, VoctoguiMiscToolbar

from vocto.port import Port
from voctogui2.ui.ui_file import ui_file


@Gtk.Template(filename=ui_file("voctogui.ui"))
class Ui(Adw.ApplicationWindow):
    __gtype_name__ = 'VoctoguiMainWindow'

    output_aspect_ratio = Gtk.Template.Child("output_aspect_ratio")
    audio_box = Gtk.Template.Child("audio_box")
    preview_box = Gtk.Template.Child("preview_box")
    video_main = Gtk.Template.Child("video_main")
    studioclock: StudioClock = Gtk.Template.Child()

    box_preview: VoctoguiPreviewToolbar = Gtk.Template.Child()
    preset_box: VoctoguiPresetToolbar = Gtk.Template.Child()
    box_insert: VoctoguiOverlayToolbar = Gtk.Template.Child()
    box_blinds: VoctoguiBlinderToolbar = Gtk.Template.Child()
    toolbar_main: VoctoguiMiscToolbar = Gtk.Template.Child()

    toolbar_mix: Gtk.Box = Gtk.Template.Child()
    toolbar_mix1: Gtk.Box = Gtk.Template.Child()

    ports_win: VoctoguiPortsWindow = Gtk.Template.Child()
    queue_win: VoctoguiQueueWindow = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.log = logging.getLogger('Ui')

    def setup(self):
        self.log.info('Initializing Ui')

        # check for configuration option mainwindow/force_fullscreen
        if Config.getForceFullScreen():
            self.log.info(
                'Forcing main window to full screen by configuration')
            # set window into fullscreen mode
            self.fullscreen()
        else:
            # check for configuration option mainwindow/width and /height
            if Config.getWindowSize():
                # set window size
                self.set_size_request(*Config.getWindowSize())
                self.set_resizable(False)

        self.output_aspect_ratio.props.ratio = Config.getVideoRatio()

        # Setup Preview Controller
        self.video_previews = VideoPreviewsController(
            self.preview_box,
            self.audio_box,
        )
        if Config.getPreviewsEnabled():
            for idx, source in enumerate(Config.getSources()):
                self.video_previews.addPreview(source, Port.SOURCES_PREVIEW + idx)
        elif Config.getMirrorsEnabled():
            for idx, source in enumerate(Config.getMirrorsSources()):
                self.video_previews.addPreview(source, Port.SOURCES_OUT + idx)
        else:
            self.log.warning(
                'Can not show source previews because neither previews nor mirrors are enabled (see previews/enabled and mirrors/enabled in core configuration)')

        self.mix_audio_display = AudioDisplay(self.audio_box, "mix", self)

        # Create Main-Video Display
        self.mix_video_display = VideoDisplay(
            self.video_main,
            self.mix_audio_display,
            port=Port.MIX_PREVIEW if Config.getPreviewsEnabled() else Port.MIX_OUT,
            name="MIX",
            play_audio=Config.getPlayAudio(),
        )

        for idx, livepreview in enumerate(Config.getLivePreviews()):
            if Config.getPreviewsEnabled():
                self.video_previews.addPreview(
                    '{}-blinded'.format(livepreview), Port.LIVE_PREVIEW + idx, has_volume=False)
            else:
                self.video_previews.addPreview(
                    '{}-blinded'.format(livepreview), Port.LIVE_OUT + idx, has_volume=False)

        self.preview_toolbar_controller = PreviewToolbarController(self.box_preview)

        self.preset_controller = PresetController(
            self.preset_box,
            preview_controller=self.preview_toolbar_controller,
        )

        self.overlay_toolbar_controller = OverlayToolbarController(
            self.box_insert,
        )

        self.mix_toolbar_controller = MixToolbarController(
            self.toolbar_mix,
            self.toolbar_mix1,
            preview_controller=self.preview_toolbar_controller,
            overlay_controller=self.overlay_toolbar_controller
        )

        self.blinder_toolbar_controller = BlinderToolbarController(self.box_blinds)

        self.queues_controller = QueuesWindowController(self.queue_win)
        self.ports_controller = PortsWindowController(self.ports_win)

        self.misc_controller = MiscToolbarController(
            self,
            self.toolbar_main,
            queues_controller=self.queues_controller,
            ports_controller=self.ports_controller,
            video_display=self.mix_video_display
        )

        # Setup Shortcuts window
        #self.connect('state-event', self.handle_state)

    def handle_state(self, window, event):
        # force full screen if whished by configuration
        if Config.getForceFullScreen():
            self.log.info('re-forcing fullscreen mode')
            self.fullscreen()

    def show(self):
        self.log.info('Showing Main-Window')
        self.present()
