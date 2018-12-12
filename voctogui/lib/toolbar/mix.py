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

    def __init__(self, win, uibuilder, output_controller, preview_controller):
        self.initialized = False
        self.output_controller = output_controller
        self.preview_controller = preview_controller
        self.log = logging.getLogger('PreviewToolbarController')

        self.toolbar = uibuilder.find_widget_recursive(
            win, 'toolbar_mix')

        uibuilder.find_widget_recursive(
            win, 'mix_retake').connect('clicked', self.on_retake_clicked)
        uibuilder.find_widget_recursive(
            win, 'mix_cut').connect('clicked', self.on_cut_clicked)
        uibuilder.find_widget_recursive(
            win, 'mix_trans').connect('clicked', self.on_trans_clicked)

    def on_retake_clicked(self, btn):
        self.preview_controller.set_command(self.output_controller.command())

    def on_cut_clicked(self, btn):
        command = self.preview_controller.command()
        self.preview_controller.set_command(self.output_controller.command())
        self.log.info('Sending new composite: %s', command)
        Connection.send('cut', str(command))

    def on_trans_clicked(self, btn):
        command = self.preview_controller.command()
        self.preview_controller.set_command(self.output_controller.command())
        self.log.info('Sending new composite (using transition): %s', command)
        Connection.send('transition', str(command))
