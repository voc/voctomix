#!/usr/bin/env python3
import gi

# import GStreamer and GLib-Helper classes
gi.require_version('Gtk', '3.0')
gi.require_version('Gst', '1.0')
gi.require_version('GstVideo', '1.0')
gi.require_version('GstNet', '1.0')

from gi.repository import Gtk, Gdk, Gst, GstVideo
import signal
import logging
import sys
import os

sys.path.insert(0, '.')
import vocto

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

Gdk.init([])
Gtk.init([])

# select Awaita:Dark theme
settings = Gtk.Settings.get_default()
settings.set_property("gtk-theme-name", "Adwaita")
settings.set_property("gtk-application-prefer-dark-theme", True)  # if you want use dark theme, set second arg to True


# main class
class Voctogui(object):

    def __init__(self):
        self.log = logging.getLogger('Voctogui')
        from lib.args import Args
        from lib.ui import Ui

        # Uf a UI-File was specified on the Command-Line, load it
        if Args.ui_file:
            self.log.info(
                'loading ui-file from file specified on command-line: %s',
                Args.ui_file
            )
            self.ui = Ui(Args.ui_file)
        else:
            # Paths to look for the gst-switch UI-File
            paths = [
                os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             'ui/voctogui.ui'),
                '/usr/lib/voctogui/ui/voctogui.ui'
            ]

            # Look for a gst-switch UI-File and load it
            self.ui = None
            for path in paths:
                self.log.debug('trying to load ui-file from file %s', path)

                if os.path.isfile(path):
                    self.log.info('Loading ui-file from file %s', path)
                    self.ui = Ui(path)
                    break

        if self.ui is None:
            raise Exception("Can't find any .ui-Files to use "
                            "(searched {})".format(', '.join(paths)))

        #
        # search for a .css style sheet file and load it
        #

        css_provider = Gtk.CssProvider()
        context = Gtk.StyleContext()

        css_paths = [
            os.path.join(os.path.dirname(os.path.realpath(__file__)),
                         'ui/voctogui.css'),
            '/usr/lib/voctogui/ui/voctogui.css'
        ]

        for path in css_paths:
            self.log.debug('trying to load css-file from file %s', path)

            if os.path.isfile(path):
                self.log.info('Loading css-file from file %s', path)
                css_provider.load_from_path(path)
                break
        else:
            raise Exception("Can't find any .css-Files to use "
                            "(searched {})".format(', '.join(css_paths)))

        context.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_USER
        )

        self.ui.setup()

    def run(self):
        self.log.info('Setting UI visible')
        self.ui.show()

        try:
            self.log.info('Running Gtk-MainLoop')
            Gtk.main()
            self.log.info('Gtk-MainLoop ended')
        except KeyboardInterrupt:
            self.log.info('Terminated via Ctrl-C')

    def quit(self):
        self.log.info('Quitting Gtk-MainLoop')
        Gtk.main_quit()


# run mainclass
def main():
    # parse command-line args
    from lib import args
    args.parse()

    from lib.args import Args
    docolor = (Args.color == 'always') \
        or (Args.color == 'auto' and sys.stderr.isatty())

    from lib.loghandler import LogHandler
    handler = LogHandler(docolor, Args.timestamp)
    logging.root.addHandler(handler)

    if Args.verbose >= 2:
        level = logging.DEBUG
    elif Args.verbose == 1:
        level = logging.INFO
    else:
        level = logging.WARNING

    logging.root.setLevel(level)

    # make killable by ctrl-c
    logging.debug('setting SIGINT handler')
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    logging.info('Python Version: %s', sys.version_info)
    logging.info('GStreamer Version: %s', Gst.version())

    logging.debug('loading Config')
    from lib import config
    config.load()

    from lib.config import Config

    # establish a synchronus connection to server
    import lib.connection as Connection
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
    if not Config.getUsePreviews() and Config.getHost() not in localhosts:
        logging.warning(
            'Connecting to `%s` (which looks like a remote host) '
            'might not work without enabeling the preview encoders '
            '(set `[previews] enabled=true` on the core) or it might saturate '
            'your ethernet link between the two machines.',
            Config.getHost()
        )

    import lib.connection as Connection
    import lib.clock as ClockManager

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
