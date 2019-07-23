#!/usr/bin/env python3
import os
import logging

from gi.repository import Gtk
import lib.connection as Connection

from lib.config import Config
from lib.uibuilder import UiBuilder
from vocto.command_helpers import quote, dequote


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

            self.overlay_description = uibuilder.get_check_widget('overlay-description')

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
                Connection.send('set_overlay', quote(str(overlay_name)))
            else:
                Connection.send('hide_overlay')

    def on_overlay(self, overlay_name):
        overlay_name = dequote(overlay_name)
        if overlay_name in self.overlays:
            self.inserts.set_active(self.overlays.index(overlay_name))
            self.insert.set_active(True)
            self.log.info("overlay is '%s'", overlay_name)
        else:
            if self.overlays:
                self.inserts.set_active(0)
            self.insert.set_active(False)
            self.log.info("overlay is off")

        self.insert.set_sensitive(not self.inserts.get_active_iter() is None)
        self.initialized = True

    def on_overlays(self, title, overlays):
        overlays = [dequote(o) for o in overlays.split(",")]
        title = dequote(title)
        if title:
            self.overlay_description.set_text(title)
            self.overlay_description.show()
        else:
            self.log.info("hide")
            self.overlay_description.hide()
        self.log.info("Got list of overlays from server '%s'", overlays)
        self.store.clear()
        if overlays:
            [self.store.append([o]) for o in overlays]
        self.overlays = overlays
        Connection.send('get_overlay')

    def isAutoOff(self):
        return self.autooff.get_active()
