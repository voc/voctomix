#!/usr/bin/env python3
import copy
import logging
import os

import lib.connection as Connection
from gi.repository import Gtk
from lib.config import Config
from lib.toolbar.buttons import Buttons
from lib.uibuilder import UiBuilder

from vocto.composite_commands import CompositeCommand


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
            win, 'toolbar_preview_composite'
        )
        toolbar_a = uibuilder.find_widget_recursive(win, 'toolbar_preview_a')
        toolbar_b = uibuilder.find_widget_recursive(win, 'toolbar_preview_b')
        toolbar_mod = uibuilder.find_widget_recursive(win, 'toolbar_preview_mod')

        self.frame_b = uibuilder.find_widget_recursive(win, 'frame_preview_b')

        # hide modify box if not needed
        box_modify = uibuilder.find_widget_recursive(win, 'box_preview_modify')
        if not Config.getToolbarMods():
            box_modify.hide()
            box_modify.set_no_show_all(True)

        self.composites.create(toolbar_composite, accelerators, self.on_btn_toggled)
        self.sourcesA.create(toolbar_a, accelerators, self.on_btn_toggled)
        self.sourcesB.create(toolbar_b, accelerators, self.on_btn_toggled)
        self.mods.create(toolbar_mod, accelerators, self.on_btn_toggled, group=False)

        self.invalid_buttons = []
        self.validate(self.sourcesA)
        self.validate(self.sourcesB)

        # initialize source buttons
        self.sourceA = Config.getVideoSources()[0]
        self.sourceB = Config.getVideoSources()[1]
        self.sourcesA[self.sourceA]['button'].set_active(True)
        self.sourcesB[self.sourceB]['button'].set_active(True)

        self.composite = self.composites.ids[0]
        self.composites[self.composite]['button'].set_active(True)

        self.modstates = dict()
        for id in self.mods.ids:
            self.modstates[id] = False

        # load composites from config
        self.log.info("Reading transitions configuration...")
        self.composites_ = Config.getComposites()

        Connection.on('best', self.on_best)
        Connection.on('composite', self.on_composite)
        Connection.send('get_composite')
        self.enable_modifiers()
        self.enable_sourcesB()
        self.enable_sources()

        self.do_test = True
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
                    if id in self.sourcesB and self.sourcesB[id]['button'].get_active():
                        self.sourceB = None
                        self.sourcesB[self.sourceA]['button'].set_active(True)
                    self.sourceA = id
                    self.log.info("Selected '%s' for preview source A", self.sourceA)
                elif self.sourcesB[id]['button'] == btn:
                    if self.sourcesA[id]['button'].get_active():
                        self.sourceA = None
                        self.sourcesA[self.sourceB]['button'].set_active(True)
                    self.sourceB = id
                    self.log.info("Selected '%s' for preview source B", self.sourceB)
                self.test()
            elif id in self.composites:
                self.composite = id
                self.enable_sourcesB()
                self.enable_modifiers()
                self.log.info(
                    "Selected '%s' for preview target composite", self.composite
                )
                self.test()
        if id in self.mods:
            self.modstates[id] = btn.get_active()
            self.log.info(
                "Turned preview modifier '%s' %s",
                id,
                'on' if self.modstates[id] else 'off',
            )
            self.test()
        self.enable_sources()
        self.log.debug("current command is '%s", self.command())

    def enable_modifiers(self):
        command = CompositeCommand(self.composite, self.sourceA, self.sourceB)
        for id, attr in self.mods.items():
            attr['button'].set_sensitive(command.modify(attr['replace']))

    def enable_sourcesB(self):
        single = self.composites_[self.composite].single()
        self.frame_b.set_sensitive(not single)

    def enable_sources(self):
        for invalid_button in self.invalid_buttons:
            invalid_button.set_sensitive(False)

    def command(self):
        # process all selected replactions
        command = CompositeCommand(self.composite, self.sourceA, self.sourceB)
        for id, attr in self.mods.items():
            if self.modstates[id]:
                command.modify(attr['replace'])
        return command

    def test(self):
        if self.do_test:
            if self.sourceA == self.sourceB:
                return False
            self.log.info("Testing transition to '%s'", str(self.command()))
            Connection.send('best', str(self.command()))

    def set_command(self, command, do_test=True):
        self.do_test = do_test
        self.log.info("Changing new composite to '%s'", str(self.command()))
        if isinstance(command, str):
            command = CompositeCommand.from_str(command)
        for id, item in self.mods.items():
            item['button'].set_active(command.modify(item['replace'], reverse=True))
        self.composites[command.composite]['button'].set_active(True)
        self.sourcesA[command.A]['button'].set_active(True)
        self.sourcesB[command.B]['button'].set_active(True)
        self.test()
        self.do_test = True

    def on_best(self, best, targetA, targetB):
        c = self.command()
        if (c.A, c.B) != (targetA, targetB) and (c.A, c.B) != (targetB, targetA):
            c.A = targetA
            c.B = targetB
            self.do_test = False
            self.set_command(c)
            self.do_test = True
        self.update_glow()

    def on_composite(self, command):
        self.output = CompositeCommand.from_str(command)
        self.test()

    def update_glow(self):
        output = copy.copy(self.output)
        for id, item in self.sourcesA.items():
            if id == output.A:
                item['button'].get_style_context().add_class("glow")
            else:
                item['button'].get_style_context().remove_class("glow")
        single = self.composites_[self.composite].single()
        output_single = self.composites_[output.composite].single()
        for id, item in self.sourcesB.items():
            if id == output.B:
                if output_single:
                    item['button'].get_style_context().remove_class("glow")
                elif single:
                    self.sourcesA[id]['button'].get_style_context().add_class("glow")
                    item['button'].get_style_context().remove_class("glow")
                else:
                    item['button'].get_style_context().add_class("glow")
            else:
                item['button'].get_style_context().remove_class("glow")
        for id, item in self.mods.items():
            if output.unmodify(item['replace']):
                item['button'].get_style_context().add_class("glow")
            else:
                item['button'].get_style_context().remove_class("glow")
        for id, item in self.composites.items():
            if id == output.composite:
                item['button'].get_style_context().add_class("glow")
            else:
                item['button'].get_style_context().remove_class("glow")

    def validate(self, sources):
        for id, attr in sources.items():
            if id not in Config.getSources():
                self.invalid_buttons.append(attr['button'])
