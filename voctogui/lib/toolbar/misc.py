#!/usr/bin/env python3
import logging
from gi.repository import Gtk

from lib.config import Config
import lib.connection as Connection


class MiscToolbarController(object):
    """Manages Accelerators and Clicks Misc buttons"""

    def __init__(self, win, uibuilder, queues_controller):
        self.log = logging.getLogger('MiscToolbarController')
        self.toolbar = uibuilder.find_widget_recursive(win, 'toolbar_main')

        # Accelerators
        accelerators = Gtk.AccelGroup()
        win.add_accel_group(accelerators)

        closebtn = uibuilder.find_widget_recursive(self.toolbar, 'close')
        closebtn.set_visible(Config.getboolean('misc', 'close'))
        closebtn.connect('clicked', self.on_closebtn_clicked)

        queues_button = uibuilder.find_widget_recursive(self.toolbar, 'queue_button')
        queues_button.set_visible(Config.getboolean('misc', 'debug'))
        queues_button.connect('toggled', self.on_queues_button_toggled)
        self.queues_controller = queues_controller

        key, mod = Gtk.accelerator_parse('t')
        #cutbtn.add_accelerator('clicked', accelerators,
        #                       key, mod, Gtk.AccelFlags.VISIBLE)
        tooltip = Gtk.accelerator_get_label(key, mod)
        #cutbtn.set_tooltip_text(tooltip)

    def on_closebtn_clicked(self, btn):
        self.log.info('close-button clicked')
        Gtk.main_quit()

    def on_queues_button_toggled(self, btn):
        self.log.info('queues-button clicked')
        self.queues_controller.show(btn.get_active())
