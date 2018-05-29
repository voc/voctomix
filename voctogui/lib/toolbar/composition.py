import logging

from gi.repository import Gtk
import lib.connection as Connection

from lib.config import Config


class CompositionToolbarController(object):
    """Manages Accelerators and Clicks on the Composition Toolbar-Buttons"""

    def __init__(self, toolbar, win, uibuilder):
        self.log = logging.getLogger('CompositionToolbarController')

        self.toolbar = toolbar
        self.uibuilder = uibuilder
        self.accelerators = Gtk.AccelGroup()
        win.add_accel_group(self.accelerators)

        composites = [
            'picture_in_picture',
            'side_by_side_equal',
            'side_by_side_preview'
        ]

        sources = Config.getlist('mix', 'sources')

        self.composite_btns = {}
        self.current_composition = None

        self.fullscreen_btn = uibuilder.find_widget_recursive(
            toolbar, 'composite-fullscreen')

        self.fullscreen_btn_pos = toolbar.get_item_index(self.fullscreen_btn)

        # Primary Fullscreen (ie. Slides) = F1
        button_idx = 0
        idx, name = self.select_primary_fullscreen_button(sources)
        print("primary", idx, name)
        self.add_fullscreen_button(button_idx, name, 'F%u' % 1)
        button_idx += 1

        # Secondary Fullscreen (ie. Cams) = 1,2,3,…
        for idx, name in self.select_secondary_fullscreen_buttons(sources):
            print("secondary", idx, name)
            self.add_fullscreen_button(button_idx, name, '%u' % (idx + 1))
            button_idx += 1

        # Composites = F2-F4
        for idx, name in enumerate(composites):
            self.add_composite_button(idx, name, 'F%u' % (idx + 2))

        # connect event-handler and request initial state
        Connection.on('composite_mode_and_video_status',
                      self.on_composite_mode_and_video_status)

        Connection.send('get_composite_mode_and_video_status')

    def add_fullscreen_button(self, index, name, accel_key):
        key, mod = Gtk.accelerator_parse(accel_key)

        if index == 0:
            new_btn = self.fullscreen_btn
        else:
            new_icon = Gtk.Image.new_from_pixbuf(
                self.fullscreen_btn.get_icon_widget().get_pixbuf())
            new_btn = Gtk.RadioToolButton(group=self.fullscreen_btn)
            new_btn.set_icon_widget(new_icon)
            self.toolbar.insert(new_btn, self.fullscreen_btn_pos + index)

        new_btn.set_label("Fullscreen %s\n%s" % (name, accel_key))
        new_btn.connect('toggled', self.on_btn_toggled)
        new_btn.set_name('fullscreen %s' % name)

        tooltip = Gtk.accelerator_get_label(key, mod)
        new_btn.set_tooltip_text(tooltip)

        new_btn.get_child().add_accelerator(
            'clicked', self.accelerators,
            key, mod, Gtk.AccelFlags.VISIBLE)

        self.composite_btns['fullscreen %s' % name] = new_btn

    def add_composite_button(self, index, name, accel_key):
        key, mod = Gtk.accelerator_parse(accel_key)

        btn = self.uibuilder.find_widget_recursive(
            self.toolbar,
            'composite-' + name.replace('_', '-')
        )
        btn.set_name(name)

        btn.set_label(btn.get_label() + "\n%s" % accel_key)

        tooltip = Gtk.accelerator_get_label(key, mod)
        btn.set_tooltip_text(tooltip)

        # Thanks to http://stackoverflow.com/a/19739855/1659732
        btn.get_child().add_accelerator('clicked', self.accelerators,
                                        key, mod, Gtk.AccelFlags.VISIBLE)
        btn.connect('toggled', self.on_btn_toggled)

        self.composite_btns[name] = btn

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

    def select_primary_fullscreen_button(self, sources):
        slide_source = Config.get('mix', 'slides_source_name', fallback=None)
        print("slide_source", slide_source)
        for idx, name in enumerate(sources):
            if name == slide_source:
                return idx, name

        return 0, sources[0]

    def select_secondary_fullscreen_buttons(self, sources):
        primary_idx, _ = self.select_primary_fullscreen_button(sources)
        for idx, name in enumerate(sources):
            if idx != primary_idx:
                yield idx, name
