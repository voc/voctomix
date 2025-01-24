#!/usr/bin/env python3
import os
import logging

from gi.repository import Gtk
import voctogui.lib.connection as Connection

from voctogui.lib.config import Config
from voctogui.lib.uibuilder import UiBuilder
from voctogui.lib.toolbar.widgets import Widgets
from datetime import datetime, timedelta
from vocto.command_helpers import quote, dequote, str2bool

class OverlayToolbarController(object):
    """Manages Accelerators and Clicks on the Overlay Composition Toolbar-Buttons"""

    def __init__(self, win, uibuilder):
        self.initialized = False

        self.log = logging.getLogger('OverlayToolbarController')

        accelerators = Gtk.AccelGroup()
        win.add_accel_group(accelerators)

        if Config.hasOverlay():

            widgets = Widgets(Config.getToolbarInsert())

            # connect to inserts selection combo box
            self.inserts = uibuilder.get_check_widget('inserts')
            self.inserts_store = uibuilder.get_check_widget('insert-store')
            self.inserts.connect('changed', self.on_inserts_changed)

            # connect to INSERT toggle button
            self.insert = uibuilder.get_check_widget('insert')
            widgets.add(self.insert, 'insert', accelerators, self.on_insert_toggled, signal='toggled' )

            self.update_inserts = uibuilder.get_check_widget('update-inserts')
            widgets.add(self.update_inserts, 'update', accelerators, self.update_overlays)

            # initialize to AUTO-OFF toggle button
            self.autooff = uibuilder.get_check_widget('insert-auto-off')
            self.autooff.set_visible(Config.getOverlayUserAutoOff())
            self.autooff.set_active(Config.getOverlayAutoOff())
            widgets.add(self.autooff, 'auto-off', accelerators)

            # remember overlay description label
            self.overlay_description = uibuilder.get_check_widget(
                'overlay-description')

            # initialize our overlay list until we get one from the core
            self.overlays = []

            # what we receive from core
            Connection.on('overlays', self.on_overlays)
            Connection.on('overlays_title', self.on_overlays_title)
            Connection.on('overlay', self.on_overlay)
            Connection.on('overlay_visible', self.on_overlay_visible)
            # call core for a list of available overlays
            self.update_overlays()
            # show insert tool bar
            uibuilder.get_check_widget('box_insert').show()
        else:
            # hide insert tool bar
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
            selected_overlay = self.inserts_store[self.inserts.get_active_iter(
            )][0]
            # tell log about user selection
            self.log.info("setting overlay to '%s'", selected_overlay)
            # hide overlay if 'AUTO-OFF' is selected
            if self.isAutoOff():
                Connection.send('show_overlay', str(False))
            # select overlay on voctocore
            Connection.send('set_overlay', quote(str(selected_overlay)))

    def on_overlay_visible(self, visible):
        ''' receive overlay visibility
        '''
        # set 'insert' button state
        self.insert.set_active(str2bool(visible))

    def on_overlay(self, overlay):
        # decode parameter
        overlay = dequote(overlay)
        overlays = [o for o, t in self.overlays]
        # do we know this overlay?
        if overlay in overlays:
            # select overlay by name
            self.inserts.set_active(overlays.index(overlay))
        else:
            if self.overlays:
                # select first item as default
                self.inserts.set_active(0)
        # tell log about new overlay
        self.log.info("overlay is '%s'", overlay)
        # enable 'INSERT' button if there is a selection
        self.insert.set_sensitive(not self.inserts.get_active_iter() is None)

    def on_overlays(self, overlays=None):
        if overlays is None:
            return
        # decode parameter
        overlays = [dequote(o).split('|') for o in overlays.split(",")]
        overlays = [o if len(o) == 2 else (o[0], o[0]) for o in overlays]
        # tell log about overlay list
        self.log.info("Got list of overlays from server '%s'", overlays)
        # clear inserts storage
        self.inserts_store.clear()
        # save inserts into storage if there are any
        if overlays:
            for o in overlays:
                self.inserts_store.append(o)
        # enable selection widget only if available
        self.inserts.set_sensitive(len(overlays) > 1 if overlays else False)
        # remember overlay list
        self.overlays = overlays
        # we have a list of overlays
        self.initialized = True
        # poll voctocore's current overlay selection
        Connection.send('get_overlay_visible')
        Connection.send('get_overlay')

    def on_overlays_title(self, title):
        # decode parameter
        title = [dequote(t) for t in title.split(",")]
        # title given?
        if title:
            # show title
            if len(title) == 4:
                start, end, id, text = title
                self.overlay_description.set_text(
                    "{start} - {end} : #{id}  '{text}'".format(start=start.split(" ")[1],
                                                               end=end.split(" ")[1],
                                                               id=id,
                                                               text=text))
            else:
                self.overlay_description.set_text(title[0])
            self.overlay_description.show()
        else:
            # hide title
            self.overlay_description.hide()
        # tell log about overlay list
        self.log.info("Got title of overlays from server '%s'", title)

    def update_overlays(self,btn=None):
        Connection.send('get_overlays')
        Connection.send('get_overlays_title')

    def isAutoOff(self):
        if Config.hasOverlay():
            return self.autooff.get_active()
