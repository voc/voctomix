#!/usr/bin/env python3
import os
import logging

from gi.repository import Gtk
import lib.connection as Connection

from lib.config import Config
from vocto.composite_commands import CompositeCommand
from lib.toolbar.buttons import Buttons
from lib.uibuilder import UiBuilder


class MixToolbarController(object):
    """Manages Accelerators and Clicks on the Preview Composition Toolbar-Buttons"""

    def __init__(self, win, uibuilder, output_controller, preview_controller, overlay_controller):
        self.initialized = False
        self.output_controller = output_controller
        self.preview_controller = preview_controller
        self.overlay_controller = overlay_controller
        self.log = logging.getLogger('PreviewToolbarController')

        accelerators = Gtk.AccelGroup()
        win.add_accel_group(accelerators)

        self.mix = Buttons(Config.getToolbarMix())

        self.toolbar = uibuilder.find_widget_recursive(win, 'toolbar_mix')

        self.mix.create(self.toolbar, accelerators,
                        self.on_btn_clicked, radio=False)
        Connection.on('best', self.on_best)

    def on_btn_clicked(self, btn):
        id = btn.get_name()
        
        # on transition hide overlay if AUTO-OFF is on
        if self.overlay_controller.isAutoOff() and id != 'retake':
            Connection.send('show_overlay',str(False))

        command = self.preview_controller.command()
        self.preview_controller.set_command(self.output_controller.command())
        if id == 'cut':
            self.log.info('Sending new composite: %s', command)
            Connection.send('cut', str(command))
        elif id == 'trans':
            self.log.info(
                'Sending new composite (using transition): %s', command)
            Connection.send('transition', str(command))

    def on_best(self, best):
        if best == "transition":
            self.mix['trans']['button'].show()
            self.mix['cut']['button'].show()
        else:
            self.mix['trans']['button'].hide()
            if best == "cut":
                self.mix['cut']['button'].show()
            else:
                self.mix['cut']['button'].hide()
