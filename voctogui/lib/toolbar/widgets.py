#!/usr/bin/env python3
from gi.repository import Gtk
import sys

def _decode(text, multiline=True):
    ''' decode multiline text '''
    if multiline:
        text = text.replace('\\n', '\n')
    else:
        text = text.replace('\\n', ' ')
    return text


class Widgets(dict):
    ''' reads widget setup from configuration from INI file.
        shall look like this:

        myitem.name = My Item
        myitem.key = <Shift>F1
        myitem.tip = Some tooltip text

        'myitem' will be the ID of the item used to identify the button.
        'name' is an optional attribute which replaces the item ID in the button label
        'tip' is an optional attribute which will be used for a tool tip message

        additional some attributes will be added automatically:

        'id' is a copy of the ID within the attributes
        'button' is the created button instance

        an extra member 'ids' becomes a list of all available IDs
    '''

    def __init__(self, cfg_items, listname="widgets"):
        # read all config items with their attributes
        self.ids = []
        if cfg_items:
            filter = cfg_items[listname].split(
                ',') if listname in cfg_items else None
            for cfg_name, cfg_value in cfg_items.items():
                if cfg_name != listname:
                    id, attr = cfg_name.rsplit('.', 1)
                    if (filter is None) or id in filter:
                        if id not in self:
                            self.ids.append(id)
                            self[id] = dict()
                            self[id]['id'] = id
                        self[id][attr] = cfg_value

    def add(self, widget, id, accelerators=None, callback=None, signal='clicked', css=[], sensitive=True, visible=True, multiline_names=True):
        # set button properties
        widget.set_can_focus(False)
        widget.set_sensitive(sensitive)
        widget.set_visible(visible)

        # set button style class
        context = widget.get_style_context()
        for c in css:
            context.add_class(c)

        # set interaction callback
        if callback:
            widget.connect(signal, callback)

        if id in self:
            attr = self[id]

            widget.set_name(id)

            # set button label
            if 'name' in attr:
                name = _decode(attr['name'], multiline_names)
            else:
                name = id.upper()
            widget.set_label(name)

            # set button tooltip
            if 'tip' in attr:
                tip = _decode(attr['tip'])
            else:
                tip = "Select source %s" % _decode(name, False)

            # set accelerator key and tooltip
            if accelerators and 'key' in attr:
                key, mod = Gtk.accelerator_parse(attr['key'])
                widget.set_tooltip_text(
                    "%s\nKey: '%s'" % (tip, attr['key'].upper()))
                # @HACK: found no explanation why ToolItems must attach their
                # accelerators to the child window
                w = widget.get_child() if isinstance(widget,Gtk.ToolItem) else widget
                w.add_accelerator(
                    'clicked', accelerators,
                    key, mod, Gtk.AccelFlags.VISIBLE)
            else:
                widget.set_tooltip_text(tip)

            # set button tooltip
            if 'expand' in attr:
                widget.set_expand(True)
