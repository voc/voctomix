import logging
from gi.repository import Gtk

import lib.connection as Connection


class CompositionToolbarController(object):
    """Manages Accelerators and Clicks on the Composition Toolbar-Buttons"""

    def __init__(self, toolbar, win, uibuilder):
        self.log = logging.getLogger('CompositionToolbarController')

        accelerators = Gtk.AccelGroup()
        win.add_accel_group(accelerators)

        composites = [
            'fullscreen',
            'picture_in_picture',
            'side_by_side_equal',
            'side_by_side_preview'
        ]

        self.composite_btns = {}
        self.current_composition = None

        for idx, name in enumerate(composites):
            key, mod = Gtk.accelerator_parse('F%u' % (idx + 1))
            btn = uibuilder.find_widget_recursive(
                toolbar,
                'composite-' + name.replace('_', '-')
            )
            btn.set_name(name)

            tooltip = Gtk.accelerator_get_label(key, mod)
            btn.set_tooltip_text(tooltip)

            # Thanks to http://stackoverflow.com/a/19739855/1659732
            btn.get_child().add_accelerator('clicked', accelerators,
                                            key, mod, Gtk.AccelFlags.VISIBLE)
            btn.connect('toggled', self.on_btn_toggled)

            self.composite_btns[name] = btn

        # connect event-handler and request initial state
        Connection.on('composite_mode', self.on_composite_mode)
        Connection.send('get_composite_mode')

    def on_btn_toggled(self, btn):
        if not btn.get_active():
            return

        btn_name = btn.get_name()
        if self.current_composition == btn_name:
            self.log.info('composition-mode already active: %s', btn_name)
            return

        self.log.info('composition-mode activated: %s', btn_name)
        Connection.send('set_composite_mode', btn_name)

    def on_composite_mode(self, mode):
        self.log.info('on_composite_mode callback w/ mode %s', mode)
        self.current_composition = mode
        self.composite_btns[mode].set_active(True)
