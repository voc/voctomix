#!/usr/bin/env python3
from gi.repository import Gtk
import sys


class Buttons(dict):
    ''' reads toolbar buttons from configuration and adds them into a toolbar
        items from INI file can shall look like this:

        myitem.name = My Item
        myitem.key = <Shift>F1
        myitem.tip = Some tooltip text
        myitem.pos = 0

        'myitem' will be the ID of the item used to identify the button.
        'name' is an optional attribute which replaces the item ID in the button label
        'tip' is an optional attribute which will be used for a tool tip message
        'pos' is an optional attribute to set the position of the button within the toolbar.
            all items without a 'pos' attribute will be added behind in random order.

        additional some attributes will be added automatically:

        'id' is a copy of the ID within the attributes
        'button' is the created button instance

        an extra member 'ids' becomes a list of all available IDs
    '''

    def __init__(self, cfg_items):
        # read all config items whit there attributes
        self.ids = []
        for cfg_name, cfg_value in cfg_items.items():
            id, attr = cfg_name.rsplit('.', 1)
            if id not in self:
                self.ids.append(id)
                self[id] = dict()
                self[id]['id'] = id
            self[id][attr] = cfg_value

    def create(self, toolbar, accelerators=None, callback=None, css=[], group=True, radio=True, sensitive=True, visible=True, multiline_names=True):
        ''' create toolbar from read configuration items '''

        def decode(text, multiline=True):
            ''' decode multiline text '''
            if multiline:
                text = text.replace('\\n', '\n')
            else:
                text = text.replace('\\n', ' ')
            return text

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
            btn.set_can_focus(False)
            btn.set_name(id)
            btn.set_sensitive(sensitive)
            btn.set_visible_horizontal(visible)
            btn.set_visible_vertical(visible)

            # set button style class
            context = btn.get_style_context()
            for c in css:
                context.add_class(c)

            # remember created button in attributes
            attr['button'] = btn

            # set button label
            if 'name' in attr:
                name = decode(attr['name'], multiline_names)
            else:
                name = id
            btn.set_label(name)

            # set button tooltip
            if 'tip' in attr:
                tip = decode(attr['tip'])
            else:
                tip = "Select source %s" % decode(name, False)

            # set interaction callback
            if callback:
                if radio:
                    btn.connect('toggled', callback)
                else:
                    btn.connect('clicked', callback)

            # set accelerator key and tooltip
            if accelerators and 'key' in attr:
                key, mod = Gtk.accelerator_parse(attr['key'])
                btn.set_tooltip_text(
                    "%s\nKey: '%s'" % (tip, attr['key'].upper()))
                btn.get_child().add_accelerator(
                    'clicked', accelerators,
                    key, mod, Gtk.AccelFlags.VISIBLE)
            else:
                btn.set_tooltip_text(tip)

            # set button tooltip
            if 'expand' in attr:
                btn.set_expand(True)

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
