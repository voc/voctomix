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
        self.current_state = None

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

        Connection.on('best', self.on_best)
        Connection.on('composite', self.on_composite)

    def on_btn_toggled(self, btn):
        self.log.info(repr(btn))

        id = btn.get_name()
        self.log.info(id)
        if btn.get_active():
            if id not in self.buttons:
                return
            self.preview_controller.set_command(self.button_to_composites[id], False)

    def on_best(self, best, targetA, targetB):
        if f'preset_{best}_{targetA}' in self.button_to_composites:
            self.current_state = f'preset_{best}_{targetA}'
        elif f'preset_{best}_{targetA}_{targetB}' in self.button_to_composites:
            self.current_state = f'preset_{best}_{targetA}_{targetB}'
        else:
            self.current_state = None
        self.log.debug(f'on_best {best=} {targetA=} {targetB=}{self.current_state=}')
        self.update_glow()

    def on_composite(self, command):
        cmd = CompositeCommand.from_str(command)
        for name, composite in self.button_to_composites.items():
            if cmd == composite:
                self.current_state = name
                break
        else:
            self.current_state = None
        self.log.debug(f'on_composite {command=} {self.current_state=}')
        self.update_glow()

    def update_glow(self):
        for id, item in self.buttons.items():
            if id == self.current_state:
                item['button'].get_style_context().add_class("glow")
            else:
                item['button'].get_style_context().remove_class("glow")

