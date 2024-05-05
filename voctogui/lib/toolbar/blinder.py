#!/usr/bin/env python3
import logging
import os
import time

import lib.connection as Connection
from gi.repository import GLib, Gtk
from lib.config import Config


class BlinderToolbarController(object):
    """Manages Accelerators and Clicks on the Composition Toolbar-Buttons"""

    # set resolution of the blink timer in seconds
    timer_resolution = 1.0

    def __init__(self, win, uibuilder):
        self.log = logging.getLogger('BlinderToolbarController')
        self.toolbar = uibuilder.find_widget_recursive(win, 'toolbar_blinder')

        live_button = uibuilder.find_widget_recursive(self.toolbar, 'stream_live')
        blind_button = uibuilder.find_widget_recursive(self.toolbar, 'stream_blind')
        blinder_box = uibuilder.find_widget_recursive(win, 'box_blinds')

        blind_button_pos = self.toolbar.get_item_index(blind_button)

        if not Config.getBlinderEnabled():
            self.log.info(
                'disabling blinding features '
                'because the server does not support them'
            )

            self.toolbar.remove(live_button)
            self.toolbar.remove(blind_button)

            # hide blinder box
            blinder_box.hide()
            blinder_box.set_no_show_all(True)
            return

        blinder_sources = Config.getBlinderSources()

        self.current_status = None

        live_button.connect('toggled', self.on_btn_toggled)
        live_button.set_can_focus(False)
        self.live_button = live_button
        self.blind_buttons = {}

        accel_f_key = 11

        for idx, name in enumerate(blinder_sources):
            if idx == 0:
                new_btn = blind_button
            else:
                new_btn = Gtk.RadioToolButton(group=live_button)
                self.toolbar.insert(new_btn, blind_button_pos)

            new_btn.set_name(name)
            new_btn.get_style_context().add_class("output")
            new_btn.get_style_context().add_class("mode")
            new_btn.set_can_focus(False)
            new_btn.set_label(name.upper())
            new_btn.connect('toggled', self.on_btn_toggled)
            new_btn.set_tooltip_text("Stop streaming by %s" % name)

            self.blind_buttons[name] = new_btn
            accel_f_key = accel_f_key - 1

        # connect event-handler and request initial state
        Connection.on('stream_status', self.on_stream_status)
        Connection.send('get_stream_status')
        self.timeout = None

    def start_blink(self):
        self.blink = True
        self.do_timeout()
        self.blink = True
        # remove old time out
        if self.timeout:
            GLib.source_remove(self.timeout)
        # set up timeout for periodic redraw
        self.timeout = GLib.timeout_add_seconds(self.timer_resolution, self.do_timeout)

    def on_btn_toggled(self, btn):
        if btn.get_active():
            btn_name = btn.get_name()
            if self.current_status != btn_name:
                self.log.info('stream-status activated: %s', btn_name)
                if btn_name == 'live':
                    Connection.send('set_stream_live')
                else:
                    Connection.send('set_stream_blind', btn_name)

    def on_stream_status(self, status, source=None):
        self.log.info(
            'on_stream_status callback w/ status %s and source %s', status, source
        )

        self.current_status = source if source is not None else status
        for button in list(self.blind_buttons.values()) + [self.live_button]:
            if button.get_name() == self.current_status:
                button.set_active(True)
        self.start_blink()

    def do_timeout(self):
        # if time did not change since last redraw
        for button in list(self.blind_buttons.values()) + [self.live_button]:
            if self.blink:
                button.get_style_context().add_class("blink")
            else:
                button.get_style_context().remove_class("blink")
        self.blink = not self.blink
        return True
