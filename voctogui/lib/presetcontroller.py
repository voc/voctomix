#!/usr/bin/env python3
import logging
import os
import time

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

        keybindings = Config.getPresetKeybindings()
        sources_composites = Config.getPresetSourcesComposites()
        sources_fullscreen = Config.getPresetSourcesFullscreen()
        composites = Config.getPresetComposites()
        accelerators = Gtk.AccelGroup()

        buttons = {}
        self.button_to_composites = {}
        self.current_state = None

        self.log.debug(f"{keybindings=}")
        self.log.debug(f"{sources_composites=}")
        self.log.debug(f"{sources_fullscreen=}")
        self.log.debug(f"{composites=}")

        if (not sources_composites and not sources_fullscreen) or not composites:
            self.box.hide()
            self.box.set_no_show_all(True)
            return

        idx = 0
        if "fs" in composites:
            for sourceA in sources_fullscreen:
                button_name = f"preset_fs_{sourceA}"
                buttons[f"{button_name}.name"] = f"{sourceA}"
                if 'slides' in sourceA:
                    buttons[f"{button_name}.icon"] = "slides.svg"
                else:
                    buttons[f"{button_name}.icon"] = "speaker.svg"

                try:
                    buttons[f"{button_name}.key"] = keybindings[idx]
                    idx += 1
                except IndexError:
                    pass
                for sourceB in sources_fullscreen:
                    if sourceA != sourceB:
                        self.button_to_composites[button_name] = CompositeCommand(
                            "fs", sourceA, sourceB
                        )
                        break
                else:
                    self.button_to_composites[button_name] = CompositeCommand(
                        "fs", sourceA, None
                    )

        if "lec" in composites:
            for sourceA in sources_composites:
                if sourceA not in Config.getLiveSources():
                    continue
                for sourceB in sources_composites:
                    if sourceB not in Config.getLiveSources():
                        button_name = f"preset_lec_{sourceA}_{sourceB}"
                        buttons[f"{button_name}.name"] = (
                            f"{sourceA}\n{sourceB}"
                        )
                        buttons[f"{button_name}.icon"] = (
                            "side-by-side-preview.svg"
                        )

                        try:
                            buttons[f"{button_name}.key"] = keybindings[idx]
                            idx += 1
                        except IndexError:
                            pass
                        self.button_to_composites[button_name] = CompositeCommand(
                            "lec", sourceA, sourceB
                        )

        if "sbs" in composites:
            for sourceA in sources_composites:
                if sourceA not in Config.getLiveSources():
                    continue
                for sourceB in sources_composites:
                    if sourceB not in Config.getLiveSources():
                        button_name = f"preset_sbs_{sourceA}_{sourceB}"
                        buttons[f"{button_name}.name"] = (
                            f"{sourceA}\n{sourceB}"
                        )
                        buttons[f"{button_name}.icon"] = (
                            "side-by-side.svg"
                        )
                        try:
                            buttons[f"{button_name}.key"] = keybindings[idx]
                            idx += 1
                        except IndexError:
                            pass
                        self.button_to_composites[button_name] = CompositeCommand(
                            "sbs", sourceA, sourceB
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
                    composite.composite == 'fs'
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
