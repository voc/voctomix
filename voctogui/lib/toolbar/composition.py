import logging

from gi.repository import Gtk
import lib.connection as Connection

from lib.config import Config


class CompositionToolbarController(object):
    """Manages Accelerators and Clicks on the Composition Toolbar-Buttons"""

    def __init__(self, toolbar, win, uibuilder):
        self.log = logging.getLogger('CompositionToolbarController')

        accelerators = Gtk.AccelGroup()
        win.add_accel_group(accelerators)

        composites = [
            'picture_in_picture',
            'side_by_side_equal',
            'side_by_side_preview'
        ]

        sources = Config.getlist('mix', 'sources')

        self.composite_btns = {}
        self.current_composition = None

        fullscreen_btn = uibuilder.find_widget_recursive(
            toolbar, 'composite-fullscreen')

        fullscreen_btn_pos = toolbar.get_item_index(fullscreen_btn)

        accel_f_key = 1

        for idx, name in enumerate(sources):
            key, mod = Gtk.accelerator_parse('F%u' % accel_f_key)
            accel_f_key = accel_f_key + 1

            if idx == 0:
                new_btn = fullscreen_btn
            else:
                new_icon = Gtk.Image.new_from_pixbuf(
                    fullscreen_btn.get_icon_widget().get_pixbuf())
                new_btn = Gtk.RadioToolButton(group=fullscreen_btn)
                new_btn.set_icon_widget(new_icon)
                toolbar.insert(new_btn, fullscreen_btn_pos + idx)

            new_btn.set_label("Fullscreen %s" % name)
            new_btn.connect('toggled', self.on_btn_toggled)
            new_btn.set_name('fullscreen %s' % name)

            tooltip = Gtk.accelerator_get_label(key, mod)
            new_btn.set_tooltip_text(tooltip)

            new_btn.get_child().add_accelerator(
                'clicked', accelerators,
                key, mod, Gtk.AccelFlags.VISIBLE)

            self.composite_btns['fullscreen %s' % name] = new_btn

        for idx, name in enumerate(composites):
            key, mod = Gtk.accelerator_parse('F%u' % accel_f_key)
            accel_f_key = accel_f_key + 1

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
        Connection.on('composite_mode_and_video_status',
                      self.on_composite_mode_and_video_status)

        Connection.send('get_composite_mode_and_video_status')

    def on_btn_toggled(self, btn):
        if not btn.get_active():
            return

        btn_name = btn.get_name()
        self.log.info('btn_name = %s', btn_name)
        if self.current_composition == btn_name:
            self.log.info('composition-mode already active: %s', btn_name)
            return

        self.log.info('composition-mode activated: %s', btn_name)

        if btn_name.startswith('fullscreen'):
            _, source_name = btn_name.split(' ', 1)
            Connection.send('set_videos_and_composite',
                            source_name, '*', 'fullscreen')

        else:
            Connection.send('set_composite_mode', btn_name)

    def on_composite_mode_and_video_status(self, mode, source_a, source_b):
        self.log.info('composite_mode_and_video_status callback w/ '
                      'mode: %s, source a: %s, source b: %s',
                      mode, source_a, source_b)
        if mode == 'fullscreen':
            mode = 'fullscreen %s' % source_a

        self.current_composition = mode
        self.composite_btns[mode].set_active(True)
