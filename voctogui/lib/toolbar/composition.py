import logging

from gi.repository import Gtk, GdkPixbuf
import lib.connection as Connection

from lib.config import Config


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
                command, image_filename = value.split(':')
                if not first_btn:
                    first_btn = new_btn = Gtk.RadioToolButton(None)
                else:
                    new_btn = Gtk.RadioToolButton.new_from_widget(first_btn)
                new_btn.set_name(name)

                pixbuf = GdkPixbuf.Pixbuf.new_from_file(icon_path + image_filename.strip())
                image = Gtk.Image()
                image.set_from_pixbuf(pixbuf)
                new_btn.set_icon_widget(image)
                self.commands[name] = command
                new_btn.connect('toggled', self.on_btn_toggled)
                new_btn.set_label("F%s" % accel_f_key)
                new_btn.set_tooltip_text("Switch composite to %s" % command)
                new_btn.get_child().add_accelerator(
                    'clicked', accelerators,
                    key, mod, Gtk.AccelFlags.VISIBLE)

                self.composite_btns[name] = new_btn
                toolbar.insert(new_btn, pos)
                pos += 1
                accel_f_key  += 1

        # connect event-handler and request initial state
        Connection.on('composite_mode_and_video_status',
                      self.on_composite_mode_and_video_status)

        Connection.send('get_composite_mode_and_video_status')

    def on_btn_toggled(self, btn):
        if not btn.get_active():
            return
        btn_name = btn.get_name()
        self.log.info('sending command: %s', self.commands[btn.get_name()])
        Connection.send('set_composite', self.commands[btn.get_name()])

    def on_composite_mode_and_video_status(self, mode, source_a, source_b):
        self.log.info('composite_mode_and_video_status callback w/ '
                      'mode: %s, source a: %s, source b: %s',
                      mode, source_a, source_b)
        if mode == 'fullscreen':
            mode = 'fullscreen %s' % source_a

        self.current_composition = mode
        self.composite_btns[mode].set_active(True)
