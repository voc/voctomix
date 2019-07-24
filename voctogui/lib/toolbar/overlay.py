#!/usr/bin/env python3
import os
import logging

from gi.repository import Gtk
import lib.connection as Connection

from lib.config import Config
from lib.uibuilder import UiBuilder
from vocto.command_helpers import quote, dequote, str2bool


class OverlayToolbarController(object):
    """Manages Accelerators and Clicks on the Overlay Composition Toolbar-Buttons"""

    def __init__(self, win, uibuilder):
        self.initialized = False

        self.log = logging.getLogger('OverlayToolbarController')

        accelerators = Gtk.AccelGroup()
        win.add_accel_group(accelerators)

        if Config.hasOverlay():

            self.inserts = uibuilder.get_check_widget('inserts')
            self.inserts_store = uibuilder.get_check_widget('insert-store')
            self.inserts.connect('changed', self.on_inserts_changed)

            self.insert  = uibuilder.get_check_widget('insert')
            self.insert.connect('toggled', self.on_insert_toggled)

            self.autooff = uibuilder.get_check_widget('insert-auto-off')
            self.autooff.set_visible(Config.getOverlayUserAutoOff())
            self.autooff.set_active(Config.getOverlayAutoOff())

            self.overlay_description = uibuilder.get_check_widget('overlay-description')

            self.overlays = []

            Connection.on('overlays', self.on_overlays)
            Connection.on('overlay', self.on_overlay)
            Connection.on('overlay_visible', self.on_overlay_visible)
            Connection.send('get_overlays')
            uibuilder.get_check_widget('box_insert').show()
        else:
            uibuilder.get_check_widget('box_insert').hide()

        # Hint: self.initialized will be set to True in response to 'get_overlay'

    def on_insert_toggled(self, btn):
        # can't select insert, if we got no list already
        if not self.initialized:
            return
        Connection.send('show_overlay', str(self.insert.get_active()))


    def on_inserts_changed(self, combobox):
        ''' new insert was selected
        '''
        # can't select insert, if we got no list already
        if not self.initialized:
            return
        # check if there is any useful selection
        if self.inserts.get_active_iter():
            # get name of the selection
            selected_overlay = self.inserts_store[self.inserts.get_active_iter()][0]
            # tell log about user selection
            self.log.info("setting overlay to '%s'", selected_overlay)
            # hide overlay if 'AUTO-OFF' is selected
            if self.isAutoOff():
                Connection.send('show_overlay',str(False))
            # select overlay on voctocore
            Connection.send('set_overlay', quote(str(selected_overlay)))

    def on_overlay_visible(self, visible):
        ''' receive overlay visibility
        '''
        # set 'insert' button state
        self.insert.set_active(str2bool(visible))

    def on_overlay(self, overlay_name):
        # decode parameter
        overlay_name = dequote(overlay_name)
        # do we know this overlay?
        if overlay_name in self.overlays:
            # select overlay by name
            self.inserts.set_active(self.overlays.index(overlay_name))
        else:
            if self.overlays:
                # select first item as default
                self.inserts.set_active(0)
        # tell log about new overlay
        self.log.info("overlay is '%s'", overlay_name)
        # enable 'INSERT' button if there is a selection
        self.insert.set_sensitive(not self.inserts.get_active_iter() is None)

    def on_overlays(self, title, overlays):
        # decode parameters
        overlays = [dequote(o) for o in overlays.split(",")]
        title = dequote(title)
        # title given?
        if title:
            # show title
            self.overlay_description.set_text(title)
            self.overlay_description.show()
        else:
            # hide title
            self.overlay_description.hide()
        # tell log about overlay list
        self.log.info("Got list of overlays from server '%s'", overlays)
        # clear inserts storage
        self.inserts_store.clear()
        # save inserts into storage if there are any
        if overlays:
            [self.inserts_store.append([o]) for o in overlays]
        # enable selection widget only if available
        self.inserts.set_sensitive(len(overlays) > 1 if overlays else False)
        # remember overlay list
        self.overlays = overlays
        # we have a list of overlays
        self.initialized = True
        # poll voctocore's current overlay selection
        Connection.send('get_overlay_visible')
        Connection.send('get_overlay')

    def isAutoOff(self):
        return self.autooff.get_active()
