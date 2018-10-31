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

        buttons = Config.items('toolbar')

        self.composite_btns = {}
        self.current_composition = None

        pos = 0

        self.commands = dict()
        first_btn = None
        for name, value in buttons:
            command, label = value.split(':')
            if not first_btn:
                first_btn = new_btn = Gtk.RadioToolButton(None)
            else:
                new_btn = Gtk.RadioToolButton.new_from_widget(first_btn)
            new_btn.set_name(name)
            new_btn.set_label(label)
            self.commands[name] = command
            new_btn.connect('toggled', self.on_btn_toggled)
            toolbar.insert(new_btn, pos)
            pos += 1

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
