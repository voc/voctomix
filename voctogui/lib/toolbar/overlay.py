#!/usr/bin/env python3
import os
import logging

from gi.repository import Gtk
import lib.connection as Connection

from lib.config import Config
from lib.uibuilder import UiBuilder


class OverlayToolbarController(object):
    """Manages Accelerators and Clicks on the Overlay Composition Toolbar-Buttons"""

    def __init__(self, win, uibuilder):
        self.initialized = False

        self.log = logging.getLogger('OverlayToolbarController')

        accelerators = Gtk.AccelGroup()
        win.add_accel_group(accelerators)

        self.store = uibuilder.get_check_widget('insert-store')
        for file in Config.getOverlayFiles():
            self.store.append([file])

        self.inserts = uibuilder.get_check_widget('inserts')
        self.inserts.connect('changed', self.on_insert)

        self.insert  = uibuilder.get_check_widget('insert')
        self.insert.connect('toggled', self.on_insert)

        Connection.on('overlay', self.on_overlay)
        Connection.send('get_overlay')

        # Hint: self.initialized will be set to True in response to 'get_overlay'

    def on_insert(self, btn):
        if not self.initialized:
            return
        model = self.inserts.get_model()
        if self.inserts.get_active_iter():
            overlay_name = model[self.inserts.get_active_iter()][0]
            self.log.info("setting overlay to '%s'", overlay_name)
            if self.insert.get_active():
                Connection.send('set_overlay', str(overlay_name))
            else:
                Connection.send('hide_overlay')


    def on_overlay(self, overlay_name):
        if overlay_name in Config.getOverlayFiles():
            self.inserts.set_active(Config.getOverlayFiles().index(overlay_name))
            self.insert.set_active(True)
        else:
            self.insert.set_active(False)
        self.log.info("overlay is '%s'", overlay_name)
        self.initialized = True
