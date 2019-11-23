#!/usr/bin/env python3
import os
import logging

from gi.repository import Gtk
import lib.connection as Connection

from lib.config import Config
from vocto.composite_commands import CompositeCommand
from lib.toolbar.buttons import Buttons
from lib.uibuilder import UiBuilder


class PreviewToolbarController(object):
    """Manages Accelerators and Clicks on the Preview Composition Toolbar-Buttons"""

    def __init__(self, win, uibuilder):
        self.initialized = False

        self.log = logging.getLogger('PreviewToolbarController')

        accelerators = Gtk.AccelGroup()
        win.add_accel_group(accelerators)

        self.sourcesA = Buttons(Config.getToolbarSourcesA())
        self.sourcesB = Buttons(Config.getToolbarSourcesB())
        self.composites = Buttons(Config.getToolbarComposites())
        self.mods = Buttons(Config.getToolbarMods())

        toolbar_composite = uibuilder.find_widget_recursive(
            win, 'toolbar_preview_composite')
        toolbar_a = uibuilder.find_widget_recursive(win, 'toolbar_preview_a')
        toolbar_b = uibuilder.find_widget_recursive(win, 'toolbar_preview_b')
        toolbar_mod = uibuilder.find_widget_recursive(
            win, 'toolbar_preview_mod')

        # hide modify box if not needed
        box_modify = uibuilder.find_widget_recursive(win, 'box_preview_modify')
        if not Config.getToolbarMods():
            box_modify.hide()
            box_modify.set_no_show_all(True)

        self.composites.create(toolbar_composite,accelerators, self.on_btn_toggled)
        self.sourcesA.create(toolbar_a, accelerators, self.on_btn_toggled)
        self.sourcesB.create(toolbar_b, accelerators, self.on_btn_toggled)
        self.mods.create(toolbar_mod, accelerators, self.on_btn_toggled, group=False)

        # initialize source buttons
        self.sourceA = self.sourcesA.ids[0]
        self.sourceB = self.sourcesB.ids[1]
        self.sourcesA[self.sourceA]['button'].set_active(True)
        self.sourcesB[self.sourceB]['button'].set_active(True)

        self.composite = self.composites.ids[0]
        self.composites[self.composite]['button'].set_active(True)

        self.modstates = dict()
        for id in self.mods.ids:
            self.modstates[id] = False

        self.enable_modifiers()

        self.initialized = True

    def on_btn_toggled(self, btn):
        if not self.initialized:
            return

        id = btn.get_name()
        if btn.get_active():
            # sources button toggled?
            if id in self.sourcesA or id in self.sourcesB:
                # check for A and B switch to the same source and fix it
                if self.sourcesA[id]['button'] == btn:
                    if self.sourcesB[id]['button'].get_active():
                        self.sourceB = None
                        self.sourcesB[self.sourceA]['button'].set_active(True)
                    self.sourceA = id
                    self.log.info(
                        "Selected '%s' for preview source A", self.sourceA)
                elif self.sourcesB[id]['button'] == btn:
                    if self.sourcesA[id]['button'].get_active():
                        self.sourceA = None
                        self.sourcesA[self.sourceB]['button'].set_active(True)
                    self.sourceB = id
                    self.log.info(
                        "Selected '%s' for preview source B", self.sourceB)
            elif id in self.composites:
                self.composite = id
                self.enable_modifiers()
                self.log.info(
                    "Selected '%s' for preview target composite", self.composite)
            self.test()
        if id in self.mods:
            self.modstates[id] = btn.get_active()
            self.log.info("Turned preview modifier '%s' %s", id,
                          'on' if self.modstates[id] else 'off')
        self.log.debug("current command is '%s", self.command())

    def enable_modifiers(self):
        command = CompositeCommand(self.composite, self.sourceA, self.sourceB)
        for id, attr in self.mods.items():
            attr['button'].set_sensitive( command.modify(attr['replace']) )

    def command(self):
        # process all selected replactions
        command = CompositeCommand(self.composite, self.sourceA, self.sourceB)
        for id, attr in self.mods.items():
            if self.modstates[id]:
                command.modify(attr['replace'])
        return command

    def test(self):
        if self.sourceA == self.sourceB:
            return False
        self.log.info("Testing transition to '%s'", str(self.command()))
        Connection.send('test_transition', str(self.command()))

    def set_command(self, command):
        if type(command) == str:
            command = CompositeCommand.from_str(command)
        for id, attr in self.mods.items():
            attr['button'].set_active(
                command.modify(attr['replace'], reverse=True))
        self.composites[command.composite]['button'].set_active(True)
        self.sourcesA[command.A]['button'].set_active(True)
        self.sourcesB[command.B]['button'].set_active(True)
        self.test()
