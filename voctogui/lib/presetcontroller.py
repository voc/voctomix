#!/usr/bin/env python3
import logging
import os
import time
from re import match

import lib.connection as Connection
from gi.repository import GLib, Gtk
from lib.config import Config
from lib.toolbar.buttons import Buttons

from vocto.composite_commands import CompositeCommand


class PresetController(object):
    def __init__(self, win, preview_controller, uibuilder):
        self.log = logging.getLogger("PresetController")
        self.box = uibuilder.find_widget_recursive(win, "preset_box")
        self.toolbar = uibuilder.find_widget_recursive(win, "preset_toolbar")
        self.preview_controller = preview_controller

        presets = Config.getPresetOptions()
        defaults_b = Config.getVideoSources()

        buttons = {}
        self.button_to_composites = {}
        self.current_state = None

        self.log.debug(f"{presets=}")
        self.log.debug(f"{defaults_b=}")

        if not presets:
            self.box.hide()
            self.box.set_no_show_all(True)
            return

        for preset in presets:
            self.log.info(f"creating preset {preset}")
            parsed = match(r'^([^_]+)_([^_]+)(?:_([^_]+))?$', preset)
            if not parsed:
                raise RuntimeError(f"preset {preset} does not parse")
            transition, sourceA, sourceB = parsed.groups()
            self.log.debug(f"preset {preset} parses to: {transition=} {sourceA=} {sourceB=}")

            if sourceB is None:
                # We got a preset like "fs_cam1", meaning the user does
                # not care what's in channel B (either because they really
                # don't care, or if B is not visible). We need channel
                # B though, so we just take the first one from the toolbar.
                options = [
                    source
                    for source in defaults_b
                    if source != sourceA
                ]
                if not options:
                    raise RuntimeError(
                        f"preset {preset} does not specify source B "
                        "and could not determine one automatically."
                    )
                sourceB = options[0]

            button_name = f"preset_{preset}"
            buttons[f"{button_name}.name"] = Config.getPresetName(preset).replace('|', '\n')

            icon = Config.getPresetIcon(preset)
            if icon:
                buttons[f"{button_name}.icon"] = icon

            key = Config.getPresetKey(preset)
            if key:
                buttons[f"{button_name}.key"] = key

            self.button_to_composites[button_name] = CompositeCommand(
                transition, sourceA, sourceB
            )

        self.log.debug(f"{buttons=}")
        self.buttons = Buttons(buttons)
        self.buttons.create(self.toolbar, accelerators, self.on_btn_toggled)

        Connection.on("best", self.on_best)
        Connection.on("composite", self.on_composite)

    def on_btn_toggled(self, btn):
        self.log.debug(f">on_btn_toggle {btn=}")
        if btn.get_active():
            id = btn.get_name()
            self.log.info(f"Preset Button {id} was pressed")
            if id not in self.button_to_composites:
                self.log.error(f"Button {id} not found in composites!")
                return
            self.log.debug(f"{self.button_to_composites[id]=}")
            self.log.info(f"Selecting {self.button_to_composites[id]} for next scene")
            self.preview_controller.set_command(self.button_to_composites[id])
        self.log.debug(f"<on_btn_toggle {btn=}")

    def on_best(self, best, targetA, targetB):
        self.log.debug(f">on_best {best=} {targetA=} {targetB=} {self.current_state=}")
        c = self.preview_controller.command()
        for name, composite in self.button_to_composites.items():
            self.buttons[name]["button"].set_active(c == composite)
        self.log.debug(f"<on_best {best=} {targetA=} {targetB=} {self.current_state=}")
        self.update_glow()

    def on_composite(self, command):
        self.log.debug(f">on_composite {command=} {self.current_state=}")
        cmd = CompositeCommand.from_str(command)
        for name, composite in self.button_to_composites.items():
            if (
                composite.A == cmd.A
                and (
                    cmd.composite == 'fs'
                    or (
                        composite.composite == cmd.composite
                        and composite.B == cmd.B
                    )
                )
            ):
                self.current_state = name
                break
        else:
            self.current_state = None
        self.log.debug(f"<on_composite {command=} {self.current_state=}")
        self.update_glow()

    def update_glow(self):
        for id, item in self.buttons.items():
            if id == self.current_state:
                item["button"].get_style_context().add_class("glow")
            else:
                item["button"].get_style_context().remove_class("glow")
