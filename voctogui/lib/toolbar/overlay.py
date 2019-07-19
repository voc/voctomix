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

        if Config.hasOverlay():
            self.store = uibuilder.get_check_widget('insert-store')

            self.inserts = uibuilder.get_check_widget('inserts')
            self.inserts.connect('changed', self.on_insert)

            self.insert  = uibuilder.get_check_widget('insert')
            self.insert.connect('clicked', self.on_insert)

            self.autooff = uibuilder.get_check_widget('insert-auto-off')

            self.autooff.set_visible(Config.getOverlayUserAutoOff())
            self.autooff.set_active(Config.getOverlayAutoOff())
            self.overlays = []

            Connection.on('overlays', self.on_overlays)
            Connection.on('overlay', self.on_overlay)
            Connection.send('get_overlays')
            uibuilder.get_check_widget('box_insert').show()
        else:
            uibuilder.get_check_widget('box_insert').hide()

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
        if overlay_name in self.overlays :
            self.inserts.set_active(self.overlays.index(overlay_name))
            self.insert.set_active(True)
        else:
            self.insert.set_active(False)

        self.insert.set_sensitive(not self.inserts.get_active_iter() is None)
        self.log.info("overlay is '%s'", overlay_name)
        self.initialized = True

    def on_overlays(self, *overlays):
        self.log.info("Got list of overlays from server '%s'", overlays)
        self.overlays = overlays
        self.store.clear()
        for file in overlays:
            self.store.append([file])
        Connection.send('get_overlay')

    def isAutoOff(self):
        return self.autooff.get_active()
