#!/usr/bin/env python3
import os
import logging

from gi.repository import Gtk, GdkPixbuf
import lib.connection as Connection

from lib.config import Config
from vocto.composite_commands import CompositeCommand
from lib.toolbar.buttons import Buttons
from lib.uibuilder import UiBuilder


class OutputToolbarController(object):
    """Manages Accelerators and Clicks on the Preview Composition Toolbar-Buttons"""

    def __init__(self, win, uibuilder):
        self.log = logging.getLogger('OutputToolbarController')
        self.toolbar = uibuilder.find_widget_recursive(win, 'toolbar_output')

        self.sources = Buttons(Config['toolbar.sources.a'])
        self.targets = Buttons(Config['toolbar.targets'])
        self.mods = Buttons(Config['toolbar.mods'])

        self.sources.create(self.toolbar, css=["output", "source"], sensitive=False, visible=False)
        self.targets.create(self.toolbar, css=["output", "composite"], sensitive=False, visible=False)
        self.mods.create(self.toolbar, css=["output", "mod"], sensitive=False, visible=False)

        # connect event-handler and request initial state
        Connection.on('composite_mode_and_video_status',
                      self.on_composite_mode_and_video_status)
        Connection.on('composite',
                      self.on_composite)

        Connection.send('get_composite')


    def set_command(self,command):
        if type(command) == str:
            command = CompositeCommand.from_str(command)
        selection = []
        for id, attr in self.mods.items():
            if command.modify(attr['replace'], reverse=True):
                selection.append(id)
        selection = [command.A, command.B, command.composite] + selection

        self._command = command

        for id, attr in {**self.sources, **self.targets, **self.mods}.items():
            visible = id in selection
            attr['button'].set_visible_horizontal(visible)
            attr['button'].set_visible_vertical(visible)
        self.toolbar.rebuild_menu()

    def command(self):
        return self._command

    def on_composite(self, command):
        self.log.info('on_composite callback %s', command)
        self.set_command(command)

    def on_composite_mode_and_video_status(self, mode, source_a, source_b):
        self.on_composite(str(CompositeCommand(mode, source_a, source_b)))
