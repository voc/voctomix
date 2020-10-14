"""
vocotocore logging
"""

import sys
import logging
import time
from logging import getLogger  # noqa

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstNet', '1.0')
from gi.repository import Gst, GLib
from vocto.debug import gst_log_messages


def configure_from_args(args):
    """setup logging with cli flags"""
    docolor = (args.color == 'always') \
        or (args.color == 'auto' and sys.stderr.isatty())

    handler = LogHandler(docolor, args.timestamp)
    logging.root.addHandler(handler)

    # Set application logging facility level
    levels = {
        3: logging.DEBUG,
        2: logging.INFO,
        1: logging.WARNING,
        0: logging.ERROR,
    }
    logging.root.setLevel(levels[args.verbose])

    # Set gstreamer logging
    gst_levels = {
        3: Gst.DebugLevel.DEBUG,
        2: Gst.DebugLevel.INFO,
        1: Gst.DebugLevel.WARNING,
        0: Gst.DebugLevel.ERROR,
    }
    gst_log_messages(gst_levels[args.gstreamer_log])


class LogFormatter(logging.Formatter):
    """Format logs with colors and timestamps"""
    def __init__(self, docolor, timestamps=False):
        super().__init__()
        self.docolor = docolor
        self.timestamps = timestamps

    def formatMessage(self, record):
        if self.docolor:
            c_lvl = 33
            c_mod = 32
            c_msg = 0

            if record.levelno <= logging.DEBUG:
                c_msg = 90

            elif record.levelno <= logging.INFO:
                c_lvl = 37
                c_msg = 97

            elif record.levelno <= logging.WARNING:
                c_lvl = 31
                c_msg = 33

            else:
                c_lvl = 31
                c_mod = 31
                c_msg = 31

            fmt = ''.join([
                '\x1b[%dm' % c_lvl,  # set levelname color
                '%(levelname)8s',    # print levelname
                '\x1b[0m',           # reset formatting
                '\x1b[%dm' % c_mod,  # set name color
                ' %(name)s',         # print name
                '\x1b[%dm' % c_msg,  # set message color
                ': %(message)s',     # print message
                '\x1b[0m'            # reset formatting
            ])
        else:
            fmt = '%(levelname)8s %(name)s: %(message)s'

        if self.timestamps:
            fmt = '%(asctime)s ' + fmt

        if 'asctime' not in record.__dict__:
            record.__dict__['asctime'] = time.strftime(
                "%Y-%m-%d %H:%M:%S",
                time.localtime(record.__dict__['created'])
            )

        return fmt % record.__dict__


class LogHandler(logging.StreamHandler):
    """Handler with custom log formatter"""
    def __init__(self, docolor, timestamps):
        super().__init__()
        self.setFormatter(LogFormatter(docolor, timestamps))
