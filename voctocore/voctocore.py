#!/usr/bin/env python3
import gi
import sdnotify
import signal
import logging
import sys

sys.path.insert(0, '.')
import vocto

# import GStreamer and GLib-Helper classes
gi.require_version('Gst', '1.0')
gi.require_version('GstNet', '1.0')
from gi.repository import Gst, GLib

# import local classes
from lib.loghandler import LogHandler

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
        from lib.pipeline import Pipeline
        from lib.controlserver import ControlServer

        self.log = logging.getLogger('Voctocore')
        self.log.debug('Creating GLib-MainLoop')
        self.mainloop = GLib.MainLoop()

        # initialize subsystem
        self.log.debug('Creating A/V-Pipeline')
        self.pipeline = Pipeline()

        self.log.debug('Creating ControlServer')
        self.controlserver = ControlServer(self.pipeline)

    def run(self):
        self.log.info('Running GLib-MainLoop')
        self.log.debug('\n\n====================== UP AN RUNNING ======================\n')
        try:
            self.mainloop.run()
        except KeyboardInterrupt:
            self.log.info('Terminated via Ctrl-C')

    def quit(self):
        self.log.info('Quitting GLib-MainLoop')
        self.mainloop.quit()


def logGstMessages(max_level=Gst.DebugLevel.INFO):
    gstLog = logging.getLogger('Gst')

    def logFunction(category, level, file, function, line, object, message, *user_data):
        if level == Gst.DebugLevel.WARNING:
            gstLog.warning(message.get())
        if level == Gst.DebugLevel.FIXME:
            gstLog.warning(message.get())
        elif level == Gst.DebugLevel.ERROR:
            gstLog.error(message.get())
        elif level == Gst.DebugLevel.INFO:
            gstLog.info(message.get())
        elif level == Gst.DebugLevel.DEBUG:
            gstLog.debug(message.get())

    Gst.debug_remove_log_function(None)
    Gst.debug_add_log_function(logFunction,None)
    Gst.debug_set_default_threshold(min(max_level,logging.root.level))
    Gst.debug_set_active(True)

# run mainclass
def main():
    # parse command-line args
    from lib import args
    args.parse()

    from lib.args import Args
    docolor = (Args.color == 'always') \
        or (Args.color == 'auto' and sys.stderr.isatty())

    handler = LogHandler(docolor, Args.timestamp)
    logging.root.addHandler(handler)

    if Args.verbose > 2:
        level = logging.DEBUG
    elif Args.verbose == 2:
        level = logging.INFO
    elif Args.verbose == 1:
        level = logging.WARNING
    else:
        level = logging.ERROR


    logging.root.setLevel(level)

    if Args.gstreamer_log:
        logGstMessages()
    else:
        logGstMessages(Gst.DebugLevel.ERROR)

    # make killable by ctrl-c
    logging.debug('setting SIGINT handler')
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    logging.info('Python Version: %s', sys.version_info)
    logging.info('GStreamer Version: %s', Gst.version())

    logging.debug('loading Config')
    from lib import config
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
