#!/usr/bin/env python3
import logging

from gi.repository import Gtk, GdkPixbuf
import lib.connection as Connection

from lib.config import Config
from lib.composite_commands import CompositeCommand


class CompositionToolbarController(object):
    """Manages Accelerators and Clicks on the Composition Toolbar-Buttons"""

    def __init__(self, toolbar, win, uibuilder):
        self.log = logging.getLogger('CompositionToolbarController')

        accelerators = Gtk.AccelGroup()
        win.add_accel_group(accelerators)

        icon_path = Config.get('toolbar', 'icon-path')
        if len(icon_path) > 1 and icon_path[-1] != '/':
            icon_path += '/'

        buttons = Config.items('toolbar')

        self.composite_btns = {}
        self.current_composition = None

        pos = 0

        accel_f_key = 1

        self.commands = dict()
        first_btn = None
        for name, value in buttons:
            if name not in ['icon-path']:
                key, mod = Gtk.accelerator_parse('F%u' % accel_f_key)
                command, image_filename = (v.strip() for v in value.split(':'))
                # remember command
                self.commands[name] = command
                if not first_btn:
                    first_btn = new_btn = Gtk.RadioToolButton(None)
                else:
                    new_btn = Gtk.RadioToolButton.new_from_widget(first_btn)
                new_btn.set_name(name)
                # load, create and set icon
                pixbuf = GdkPixbuf.Pixbuf.new_from_file(icon_path + image_filename)
                image = Gtk.Image()
                image.set_from_pixbuf(pixbuf)
                new_btn.set_icon_widget(image)
                # connect button toggle signal and accelerator
                new_btn.connect('toggled', self.on_btn_toggled)
                new_btn.set_label("F%s" % accel_f_key)
                new_btn.set_tooltip_text("Switch composite to %s" % command)
                new_btn.get_child().add_accelerator(
                    'clicked', accelerators,
                    key, mod, Gtk.AccelFlags.VISIBLE)
                # remember button
                self.composite_btns[name] = new_btn
                toolbar.insert(new_btn, pos)
                pos += 1
                accel_f_key  += 1

        # connect event-handler and request initial state
        Connection.on('composite', self.on_composite)
        Connection.send('get_composite')

    def on_btn_toggled(self, btn):
        if not btn.get_active():
            return
        command = self.commands[btn.get_name()]
        self.log.info('sending command: %s', command)
        Connection.send('set_composite', command)

    def on_composite(self, command):
        command = CompositeCommand.from_str(command)
        self.log.info('composite callback: %s', command)
        for name, c in self.commands.items():
            if CompositeCommand.from_str(c) == command:
                self.composite_btns[name].set_active(True)
                return
        self.log.warning("composite button not found for %s", command)
