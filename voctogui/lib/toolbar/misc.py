#!/usr/bin/env python3
import logging
from gi.repository import Gdk, Gtk

from lib.config import Config
import lib.connection as Connection


class MiscToolbarController(object):
    """Manages Accelerators and Clicks Misc buttons"""

    def __init__(self, win, uibuilder, queues_controller, ports_controller, video_display):
        self.win = win
        self.log = logging.getLogger('MiscToolbarController')
        self.toolbar = uibuilder.find_widget_recursive(win, 'toolbar_main')

        # Accelerators
        accelerators = Gtk.AccelGroup()
        win.add_accel_group(accelerators)

        closebtn = uibuilder.find_widget_recursive(self.toolbar, 'close')
        closebtn.set_visible(Config.getboolean('misc', 'close'))
        closebtn.connect('clicked', self.on_closebtn_clicked)

        fullscreenbtn = uibuilder.find_widget_recursive(self.toolbar, 'fullscreen')
        fullscreenbtn.set_visible(Config.getboolean('misc', 'fullscreen'))
        fullscreenbtn.connect('clicked', self.on_fullscreenbtn_clicked)
        key, mod = Gtk.accelerator_parse('F11')
        fullscreenbtn.add_accelerator('clicked', accelerators,
                               key, mod, Gtk.AccelFlags.VISIBLE)

        mutebtn = uibuilder.find_widget_recursive(self.toolbar, 'mute_button')
        mutebtn.set_active(not Config.getboolean('audio', 'play'))
        mutebtn.connect('clicked', self.on_mutebtn_clicked)
        self.video_display = video_display

        queues_button = uibuilder.find_widget_recursive(self.toolbar, 'queue_button')
        queues_button.set_visible(Config.getboolean('misc', 'debug'))
        queues_button.connect('toggled', self.on_queues_button_toggled)
        self.queues_controller = queues_controller

        ports_button = uibuilder.find_widget_recursive(self.toolbar, 'ports_button')
        ports_button.set_visible(Config.getboolean('misc', 'debug'))
        ports_button.connect('toggled', self.on_ports_button_toggled)
        self.ports_controller = ports_controller

        key, mod = Gtk.accelerator_parse('t')
        tooltip = Gtk.accelerator_get_label(key, mod)

	    # Controller for fullscreen behavior
        self.__is_fullscreen = False
        win.connect("window-state-event", self.on_window_state_event)

    def on_closebtn_clicked(self, btn):
        self.log.info('close-button clicked')
        Gtk.main_quit()

    def on_fullscreenbtn_clicked(self, btn):
        self.log.info('fullscreen-button clicked')
        if self.__is_fullscreen:
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
        self.__is_fullscreen = bool(ev.new_window_state & Gdk.WindowState.FULLSCREEN)
