#!/usr/bin/env python3
import gi
import sdnotify
import signal
import logging
import sys

from vocto.debug import gst_log_messages

# import GStreamer and GLib-Helper classes
gi.require_version('Gst', '1.0')
gi.require_version('GstNet', '1.0')
from gi.repository import Gst, GLib

# import local classes
from voctocore.lib.loghandler import LogHandler

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


# main class
class Voctocore(object):

    def __init__(self):
        # import local which use the config or the logging system
        # this is required, so that we can configure logging,
        # before reading the config
        from voctocore.lib.pipeline import Pipeline
        from voctocore.lib.controlserver import ControlServer

        self.log = logging.getLogger('Voctocore')
        self.log.debug('Creating GLib-MainLoop')
        self.mainloop = GLib.MainLoop()

        # initialize subsystem
        self.log.debug('Creating A/V-Pipeline')
        self.pipeline = Pipeline()

        self.log.debug('Creating ControlServer')
        self.controlserver = ControlServer(self.pipeline)

    def run(self):
        self.log.info('Running. Waiting for connections....')
        try:
            self.mainloop.run()
        except KeyboardInterrupt:
            self.log.info('Terminated via Ctrl-C')

    def quit(self):
        self.log.info('Quitting.')
        self.mainloop.quit()


# run mainclass
def main():
    # parse command-line args
    from voctocore.lib import args
    args.parse()

    from voctocore.lib.args import Args
    docolor = (Args.color == 'always') \
        or (Args.color == 'auto' and sys.stderr.isatty())

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
    from voctocore.lib import config
    config.load()

    # init main-class and main-loop
    logging.debug('initializing Voctocore')
    voctocore = Voctocore()

    # Inform systemd that we are ready
    # for use with the notify service type
    n = sdnotify.SystemdNotifier()
    n.notify("READY=1")

    logging.debug('running Voctocore')
    voctocore.run()


if __name__ == '__main__':
    try:
        main()
    except RuntimeError as e:
        logging.error(str(e))
        sys.exit(1)
