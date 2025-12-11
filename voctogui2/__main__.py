#!/usr/bin/env python3
import typing
from typing import Optional

import gi

from voctogui2.ui.ui_file import ui_file

# import GStreamer and GLib-Helper classes
gi.require_version('Gtk', '4.0')
gi.require_version('Gst', '1.0')
gi.require_version('GstVideo', '1.0')
gi.require_version('GstNet', '1.0')
gi.require_version('Adw', '1')
from gi.repository import Adw, Gtk, Gdk, Gst, GstVideo, GLib

import signal
import logging
import sys
import os

from vocto.debug import gst_log_messages
from vocto.sd_notify import sd_notify

Gst.init()

class VoctoguiApplication(Adw.Application):
    log: logging.Logger
    ui: Optional['Ui']

    def __init__(self):
        super().__init__(application_id='com.example.TextViewer')
        self.log = logging.getLogger('VoctoguiApplication')
        self.ui = None

        icon_theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
        icon_theme.add_search_path(ui_file("icons"))

        style_manager = Adw.StyleManager.get_default()
        style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)

        css_provider = Gtk.CssProvider()
        css_provider.load_from_path(ui_file('voctogui.css'))
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        self.connect('activate', self.on_activate)

    def on_activate(self, application: 'VoctoguiApplication'):
        if not self.ui:
            from voctogui2.lib.ui import Ui
            self.ui = Ui(application=self)
            self.ui.setup()
        self.ui.show()

# main class
class Voctogui(object):

    def __init__(self) -> None:
        self.log = logging.getLogger('Voctogui')
        self.app = VoctoguiApplication()

    def run(self) -> None:
        try:
            self.log.info('Running.')
            sd_notify.ready()
            self.app.run([])
            sd_notify.stopping()
            self.log.info('Connection lost. Exiting.')
        except KeyboardInterrupt:
            self.log.info('Terminated via Ctrl-C')

    def quit(self) -> None:
        self.log.info('Quitting.')
        self.app.quit()


# run mainclass
def main() -> None:
    # parse command-line args
    from voctogui2.lib import args
    args.parse() # type: ignore

    from voctogui2.lib.args import Args
    docolor = (Args.color == 'always') \
        or (Args.color == 'auto' and sys.stderr.isatty())

    from voctogui2.lib.loghandler import LogHandler
    handler = LogHandler(docolor, Args.timestamp)
    logging.root.addHandler(handler)

    levels = { 3 : logging.DEBUG, 2 : logging.INFO, 1 : logging.WARNING, 0 : logging.ERROR }
    logging.root.setLevel(levels[Args.verbose])

    gst_levels = { 3 : Gst.DebugLevel.DEBUG, 2 : Gst.DebugLevel.INFO, 1 : Gst.DebugLevel.WARNING, 0 : Gst.DebugLevel.ERROR }
    gst_log_messages(gst_levels[Args.gstreamer_log])

    # make killable by ctrl-c
    logging.debug('setting SIGINT handler')
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    logging.info('Python Version: %s', sys.version_info)
    logging.info('GStreamer Version: %s', Gst.version())

    logging.debug('loading Config')
    from voctogui2.lib import config
    config.load()

    from voctogui2.lib.config import Config

    # establish a synchronus connection to server
    import voctogui2.lib.connection as Connection
    Connection.establish(Config.getHost())

    # fetch config from server
    Config.fetchServerConfig()

    # Warn when connecting to a non-local core without preview-encoders enabled
    # The list-comparison is not complete
    # (one could use a local hostname or the local system ip),
    # but it's only here to warn that one might be making a mistake
    localhosts = ['::1',
                  '127.0.0.1',
                  'localhost']
    if not Config.getPreviewsEnabled() and Config.getHost() not in localhosts:
        logging.warning(
            'Connecting to `%s` (which looks like a remote host) '
            'might not work without enabeling the preview encoders '
            '(set `[previews] enabled=true` on the core) or it might saturate '
            'your ethernet link between the two machines.',
            Config.getHost()
        )

    import voctogui2.lib.connection as Connection
    import voctogui2.lib.clock as ClockManager

    # obtain network-clock
    ClockManager.obtainClock(Connection.ip)

    # switch connection to nonblocking, event-driven mode
    Connection.enterNonblockingMode()

    # init main-class and main-loop
    # (this binds all event-hander on the Connection)
    logging.debug('initializing Voctogui')
    voctogui = Voctogui()

    # start the Mainloop and show the Window
    logging.debug('running Voctogui')
    voctogui.run()


if __name__ == '__main__':
    try:
        main()
    except RuntimeError as e:
        logging.error(str(e))
        sys.exit(1)
