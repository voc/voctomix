#!/usr/bin/env python3
import os
import logging
import copy

from gi.repository import Gtk, GdkPixbuf
import lib.connection as Connection

from lib.config import Config
from vocto.composite_commands import CompositeCommand
from lib.toolbar.buttons import Buttons
from lib.uibuilder import UiBuilder


class OutputToolbarController(object):
    """Manages Accelerators and Clicks on the Preview Composition Toolbar-Buttons"""

    def __init__(self, win, uibuilder, preview_controller):
        self.log = logging.getLogger('OutputToolbarController')

        self.sourcesA = Buttons(Config.getToolbarSourcesA())
        self.sourcesB = Buttons(Config.getToolbarSourcesB())
        self.composites = Buttons(Config.getToolbarComposites())
        self.mods = Buttons(Config.getToolbarMods())

        self.toolbar_composite = uibuilder.find_widget_recursive(win, 'toolbar_output_composite')
        self.toolbar_a = uibuilder.find_widget_recursive(win, 'toolbar_output_a')
        self.toolbar_b = uibuilder.find_widget_recursive(win, 'toolbar_output_b')
        self.toolbar_mod = uibuilder.find_widget_recursive(win, 'toolbar_output_mod')

        self.preview_controller = preview_controller

        box_modify = uibuilder.find_widget_recursive(win, 'box_output_modify')
        if not Config.getToolbarMods():
            box_modify.hide()
            box_modify.set_no_show_all(True)

        self.composites.create(self.toolbar_composite, css=["output", "composite"], group=False, sensitive=False, visible=False, multiline_names=False)
        self.sourcesA.create(self.toolbar_a, css=["output", "source"], group=False, sensitive=False, visible=False, multiline_names=False)
        self.sourcesB.create(self.toolbar_b, css=["output", "source"], group=False, sensitive=False, visible=False, multiline_names=False)
        self.mods.create(self.toolbar_mod, css=["output", "mod"], group=False, sensitive=False, visible=False, multiline_names=False)

        # connect event-handler and request initial state
        Connection.on('composite_mode_and_video_status',
                      self.on_composite_mode_and_video_status)
        Connection.on('composite',
                      self.on_composite)

        Connection.send('get_composite')


    def set_command(self,command):
        if type(command) == str:
            command = CompositeCommand.from_str(command)
        self._command = copy.deepcopy(command)
        selection = []
        for id, attr in self.mods.items():
            if command.modify(attr['replace'], reverse=True):
                selection.append(id)
        selection = [command.composite] + selection

        for id, attr in self.sourcesA.items():
            visible = id == command.A
            attr['button'].set_visible_horizontal(visible)
            attr['button'].set_visible_vertical(visible)

        for id, attr in self.sourcesB.items():
            visible = id == command.B
            attr['button'].set_visible_horizontal(visible)
            attr['button'].set_visible_vertical(visible)

        for id, attr in {**self.composites, **self.mods}.items():
            visible = id in selection
            attr['button'].set_visible_horizontal(visible)
            attr['button'].set_visible_vertical(visible)

        self.toolbar_composite.rebuild_menu()
        self.toolbar_a.rebuild_menu()
        self.toolbar_b.rebuild_menu()
        self.toolbar_mod.rebuild_menu()

    def command(self):
        return self._command

    def on_composite(self, command):
        self.log.info('on_composite callback %s', command)
        self.set_command(command)
        self.preview_controller.test()

    def on_composite_mode_and_video_status(self, mode, source_a, source_b):
        self.on_composite(str(CompositeCommand(mode, source_a, source_b)))
