#!/usr/bin/env python3
import logging
import os

import time

from gi.repository import Gtk, GLib
import lib.connection as Connection

from vocto.composite_commands import CompositeCommand
from lib.config import Config
from lib.toolbar.buttons import Buttons


class PresetController(object):
    def __init__(self, win, preview_controller, uibuilder):
        self.log = logging.getLogger('PresetController')
        self.box = uibuilder.find_widget_recursive(win, 'preset_box')
        self.toolbar = uibuilder.find_widget_recursive(win, 'preset_toolbar')
        self.preview_controller = preview_controller

        sources = Config.getToolbarSourcesA()
        accelerators = Gtk.AccelGroup()

        buttons = {}
        self.button_to_composites = {}

        if 'buttons' not in sources:
            self.box.hide()
            self.box.set_no_show_all(True)
            return

        source_buttons = sources['buttons'].split(',')
        for sourceA in source_buttons:
            buttons[f'preset_fs_{sourceA}.name'] = f'FS {sourceA}'
            for sourceB in source_buttons:
                if sourceA != sourceB:
                    self.button_to_composites[f'preset_fs_{sourceA}'] = CompositeCommand('fs', sourceA, sourceB)
                    break
            else:
                self.button_to_composites[f'preset_fs_{sourceA}'] = CompositeCommand('fs', sourceA, None)

        for sourceA in source_buttons:
            if sourceA not in Config.getLiveSources():
                continue
            for sourceB in source_buttons:
                if sourceB not in Config.getLiveSources():
                    buttons[f'preset_lec_{sourceA}_{sourceB}.name'] = f'Lecture {sourceA} {sourceB}'
                    self.button_to_composites[f'preset_lec_{sourceA}_{sourceB}'] = CompositeCommand('lec', sourceA, sourceB)

        for sourceA in source_buttons:
            if sourceA not in Config.getLiveSources():
                continue
            for sourceB in source_buttons:
                if sourceB not in Config.getLiveSources():
                    buttons[f'preset_sbs_{sourceA}_{sourceB}.name'] = f'SideBySide {sourceA} {sourceB}'
                    self.button_to_composites[f'preset_sbs_{sourceA}_{sourceB}'] = CompositeCommand('sbs', sourceA, sourceB)

        self.buttons = Buttons(buttons)
        self.buttons.create(self.toolbar, accelerators, self.on_btn_toggled)


    def on_btn_toggled(self, btn):
        self.log.info(repr(btn))

        id = btn.get_name()
        self.log.info(id)
        if btn.get_active():
            if id not in self.buttons:
                return

            self.preview_controller.set_command(self.button_to_composites[id], False)
