#!/usr/bin/env python3
import gi
# import GStreamer and GLib-Helper classes
gi.require_version('Gtk', '3.0')
gi.require_version('Gst', '1.0')
gi.require_version('GstVideo', '1.0')
gi.require_version('GstNet', '1.0')
from gi.repository import Gtk, Gdk, Gst, GstVideo, GLib

import signal
import logging
import sys
import os

from vocto.debug import gst_log_messages

# check min-version
minGst = (1, 5)
minPy = (3, 0)

Gst.init([])
if Gst.version() < minGst:
    raise Exception('GStreamer version', Gst.version(),
                    'is too old, at least', minGst, 'is required')

if sys.version_info < minPy:
    raise Exception('Python version', sys.version_info,
                    'is too old, at least', minPy, 'is required')

Gdk.init([]) # type: ignore
Gtk.init([]) # type: ignore

# select window icon on wayland
GLib.set_prgname("voctogui.desktop")

# select Awaita:Dark theme
settings = Gtk.Settings.get_default()
if settings is not None:
    settings.set_property("gtk-theme-name", "Adwaita")
    settings.set_property("gtk-application-prefer-dark-theme", True)  # if you want use dark theme, set second arg to True


# main class
class Voctogui(object):

    def __init__(self) -> None:
        self.log = logging.getLogger('Voctogui')
        from voctogui.lib.args import Args
        from voctogui.lib.ui import Ui

        # Load UI file
        path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ui/voctogui.ui')
        self.log.info('Loading ui-file from file %s', path)
        if os.path.isfile(path):
            self.ui = Ui(path)
        else:
            raise Exception("Can't find any .ui-Files to use in {}".format(path))

        #
        # search for a .css style sheet file and load it
        #

        css_provider = Gtk.CssProvider()
        context = Gtk.StyleContext()

        path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ui/voctogui.css')
        self.log.info('Loading css-file from file %s', path)
        if os.path.isfile(path):
            css_provider.load_from_path(path)
        else:
            raise Exception("Can't find .css file '{}'".format(path))

        screen = Gdk.Screen.get_default()
        if screen is None:
            raise Exception("No default screen available")
        context.add_provider_for_screen(
            screen,
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_USER
        )

        self.ui.setup()

    def run(self) -> None:
        self.log.info('Setting UI visible')
        self.ui.show()

        try:
            self.log.info('Running.')
            Gtk.main()
            self.log.info('Connection lost. Exiting.')
        except KeyboardInterrupt:
            self.log.info('Terminated via Ctrl-C')

    def quit(self) -> None:
        self.log.info('Quitting.')
        Gtk.main_quit()


# run mainclass
def main() -> None:
    # parse command-line args
    from voctogui.lib import args
    args.parse() # type: ignore

    from voctogui.lib.args import Args
    docolor = (Args.color == 'always') \
        or (Args.color == 'auto' and sys.stderr.isatty())

    from voctogui.lib.loghandler import LogHandler
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
    from voctogui.lib import config
    config.load()

    from voctogui.lib.config import Config

    # establish a synchronus connection to server
    import voctogui.lib.connection as Connection
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

    import voctogui.lib.connection as Connection
    import voctogui.lib.clock as ClockManager

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
