#!/usr/bin/env python3
import logging

from gi.repository import Gdk, Gtk

from voctogui2.lib.config import Config
import voctogui2.lib.connection as Connection
from voctogui2.ui.ui_file import ui_file


@Gtk.Template(filename=ui_file("toolbar_misc.ui"))
class VoctoguiMiscToolbar(Gtk.Box):
    __gtype_name__ = 'VoctoguiMiscToolbar'

    close: Gtk.Button = Gtk.Template.Child()
    fullscreen: Gtk.ToggleButton = Gtk.Template.Child()
    mute_button: Gtk.ToggleButton = Gtk.Template.Child()
    queue_button: Gtk.ToggleButton = Gtk.Template.Child()
    ports_button: Gtk.ToggleButton = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class MiscToolbarController(object):
    """Manages Accelerators and Clicks Misc buttons"""

    win: Gtk.ApplicationWindow

    def __init__(self, window, toolbar, queues_controller, ports_controller, video_display):
        self.log = logging.getLogger('MiscToolbarController')
        self.win = window
        self.toolbar = toolbar

        # Accelerators
        #accelerators = Gtk.AccelGroup()
        #win.add_accel_group(accelerators)

        accelerators = None

        toolbar.close.set_visible(Config.getShowCloseButton())
        toolbar.close.connect('clicked', self.on_closebtn_clicked)

        toolbar.fullscreen.set_visible(Config.getShowFullScreenButton())
        toolbar.fullscreen.connect('clicked', self.on_fullscreenbtn_clicked)
        #key, mod = Gtk.accelerator_parse('F11')
        #toolbar.fullscreen.add_accelerator('clicked', accelerators,
        #                                   key, mod, Gtk.AccelFlags.VISIBLE)
        self.fullscreen_button = toolbar.fullscreen

        if Config.getPlayAudio():
            toolbar.mute_button.set_active(True)
            toolbar.mute_button.connect('clicked', self.on_mutebtn_clicked)
            self.video_display = video_display
        else:
            toolbar.mute_button.hide()

        toolbar.queue_button.set_visible(Config.getShowQueueButton())
        toolbar.queue_button.connect('toggled', self.on_queues_button_toggled)
        self.queues_controller = queues_controller

        toolbar.ports_button.set_visible(Config.getShowPortButton())
        toolbar.ports_button.connect('toggled', self.on_ports_button_toggled)
        self.ports_controller = ports_controller

        #key, mod = Gtk.accelerator_parse('t')
        #tooltip = Gtk.accelerator_get_label(key, mod)

        # Controller for fullscreen behavior
        window.connect("notify", self.on_window_state_event)

    def on_closebtn_clicked(self, btn):
        self.log.info('close-button clicked')
        self.win.get_application().quit()

    def on_fullscreenbtn_clicked(self, btn):
        self.log.info('fullscreen-button clicked')
        if self.win.is_fullscreen():
            self.win.unfullscreen()
        else:
            self.win.fullscreen()

    def on_mutebtn_clicked(self, btn):
        self.log.info('mute-button clicked')
        self.video_display.mute(not btn.get_active())

    def on_queues_button_toggled(self, btn):
        self.log.info('queues-button clicked')
        self.queues_controller.show(btn.get_active())

    def on_ports_button_toggled(self, btn):
        self.log.info('queues-button clicked')
        self.ports_controller.show(btn.get_active())

    def on_window_state_event(self, widget, ev):
        self.fullscreen_button.set_active(self.win.is_fullscreen())
