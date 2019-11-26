#!/usr/bin/env python3
from gi.repository import Gtk
import sys
from lib.toolbar.widgets import _decode, Widgets

class Buttons(Widgets):
    ''' reads toolbar buttons from configuration and adds them into a toolbar
        items from INI file can shall look like this:

        additional some attributes will be added automatically:

        'button' is the created button instance
    '''

    def __init__(self, cfg_items):
        super().__init__(cfg_items,"buttons")

    def create(self, toolbar, accelerators=None, callback=None, css=[], group=True, radio=True, sensitive=True, visible=True, multiline_names=True):
        ''' create toolbar from read configuration items '''

        # generate a list of all buttons
        buttons = []
        first_btn = None
        for id, attr in self.items():
            if radio:
                # create button and manage grouping of radio buttons
                if group:
                    if not first_btn:
                        first_btn = btn = Gtk.RadioToolButton(None)
                    else:
                        btn = Gtk.RadioToolButton.new_from_widget(first_btn)
                else:
                    btn = Gtk.ToggleToolButton()
            else:
                btn = Gtk.ToolButton()

            # set button properties
            self.add(btn, id, accelerators, callback, ('toggled' if radio else 'clicked'), css, sensitive, visible, multiline_names)
            btn.set_visible_horizontal(visible)
            btn.set_visible_vertical(visible)
            btn.set_can_focus(False)

            # remember created button in attributes
            attr['button'] = btn

            # store button
            buttons.append(
                (int(attr['pos']) if 'pos' in attr else sys.maxsize, btn))

        # add all buttons in right order
        def key(x):
            return x[0]
        pos = toolbar.get_n_items()
        for btn in sorted(buttons, key=key):
            toolbar.insert(btn[1], pos)
            pos += 1
