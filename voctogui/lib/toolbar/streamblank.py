#!/usr/bin/env python3
import logging
import os

import time

from gi.repository import Gtk, GLib
import lib.connection as Connection

from lib.config import Config


class StreamblankToolbarController(object):
    """Manages Accelerators and Clicks on the Composition Toolbar-Buttons"""

    # set resolution of the blink timer in seconds
    timer_resolution = 0.5

    def __init__(self, win, uibuilder):
        self.log = logging.getLogger('StreamblankToolbarController')
        self.toolbar = uibuilder.find_widget_recursive(win, 'toolbar_mode')

        livebtn = uibuilder.find_widget_recursive(self.toolbar, 'stream_live')
        blankbtn = uibuilder.find_widget_recursive(
            self.toolbar, 'stream_blank')

        blankbtn_pos = self.toolbar.get_item_index(blankbtn)

        if not Config.getboolean('stream-blanker', 'enabled'):
            self.log.info('disabling stream-blanker features '
                          'because the server does not support them: %s',
                          Config.getboolean('stream-blanker', 'enabled'))

            self.toolbar.remove(livebtn)
            self.toolbar.remove(blankbtn)
            return

        blank_sources = Config.getlist('stream-blanker', 'sources')

        self.current_status = None

        livebtn.connect('toggled', self.on_btn_toggled)
        livebtn.set_can_focus(False)
        self.livebtn = livebtn
        self.blank_btns = {}

        accel_f_key = 11

        for idx, name in enumerate(blank_sources):
            if idx == 0:
                new_btn = blankbtn
            else:
                new_btn = Gtk.RadioToolButton(group=livebtn)
                self.toolbar.insert(new_btn, blankbtn_pos)

            new_btn.set_name(name)
            new_btn.set_can_focus(False)
            new_btn.set_label(name.upper())
            new_btn.connect('toggled', self.on_btn_toggled)
            new_btn.set_tooltip_text("Stop streaming by %s" % name)

            self.blank_btns[name] = new_btn
            accel_f_key = accel_f_key - 1

        # connect event-handler and request initial state
        Connection.on('stream_status', self.on_stream_status)
        Connection.send('get_stream_status')

        self.blink = True
        # remember last draw time
        self.last_draw_time = time.time()
        # set up timeout for periodic redraw
        GLib.timeout_add(self.timer_resolution * 1000, self.do_timeout)

    def on_btn_toggled(self, btn):
        if btn.get_active():
            btn_name = btn.get_name()

            if self.current_status != btn_name:
                self.log.info('stream-status activated: %s', btn_name)
                if btn_name == 'live':
                    Connection.send('set_stream_live')
                else:
                    Connection.send('set_stream_blank', btn_name)

    def on_stream_status(self, status, source=None):
        self.log.info('on_stream_status callback w/ status %s and source %s',
                      status, source)

        self.current_status = source if source is not None else status

    def do_timeout(self):
        # get current time
        current_time = time.time()
        # if time did not change since last redraw
        if current_time - self.last_draw_time >= 1.0:
            self.last_draw_time = current_time
            for button in list(self.blank_btns.values()) + [self.livebtn]:
                print(button.get_name())
                if self.blink:
                    button.get_style_context().add_class("blink")
                else:
                    button.get_style_context().remove_class("blink")
            self.blink = not self.blink
        return True
