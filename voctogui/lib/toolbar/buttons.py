#!/usr/bin/env python3
from gi.repository import Gtk

class Buttons(dict):

    def __init__(self, cfg_items):
        self.ids = []
        for cfg_name, cfg_value in cfg_items.items():
            id, attr = cfg_name.rsplit('.', 1)
            if id not in self:
                self.ids.append(id)
                self[id] = dict()
                self[id]['id'] = id
            self[id][attr] = cfg_value

    def create(self, toolbar, pos, accelerators=None, toggled_callback=None, css=[], group=True, sensitive=True, visible=True):
        def decode( text, multiline=True ):
            if multiline:
                text = text.replace('\\n','\n')
            else:
                text = text.replace('\\n',' ')
            return text

        first_btn = None
        for id, attr in self.items():
            if group:
                if not first_btn:
                    first_btn = new_btn = Gtk.RadioToolButton(None)
                else:
                    new_btn = Gtk.RadioToolButton.new_from_widget(first_btn)
            else:
                new_btn = Gtk.ToggleToolButton()
            attr['button'] = new_btn
            new_btn.set_can_focus(False)
            new_btn.set_name(id)
            new_btn.set_sensitive(sensitive)
            new_btn.set_visible_horizontal(visible)
            new_btn.set_visible_vertical(visible)

            context = new_btn.get_style_context()
            for c in css:
                context.add_class(c)

            if 'name' in attr:
                name = decode(attr['name'])
            else:
                name = id
            new_btn.set_label(name)

            if 'tip' in attr:
                tip = decode(attr['tip'])
            else:
                tip = "Select source %s" % decode(name,False)

            if toggled_callback:
                new_btn.connect('toggled', toggled_callback)

            if accelerators:
                if 'key' in attr:
                    key, mod = Gtk.accelerator_parse(attr['key'])
                    new_btn.set_tooltip_text("%s\nKey: '%s'" % (tip, attr['key'].upper()))
                    new_btn.get_child().add_accelerator(
                        'clicked', accelerators,
                        key, mod, Gtk.AccelFlags.VISIBLE)
                else:
                    new_btn.set_tooltip_text(tip)

            toolbar.insert(new_btn, pos)
            pos += 1

        return pos
