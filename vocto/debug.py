#!/usr/bin/env python3
import logging
import os

import gi
from gi.repository import Gst

gi.require_version('Gst', '1.0')

log = logging.getLogger('vocto.debug')


def gst_generate_dot(pipeline, name):
    from lib.args import Args

    dotfile = os.path.join(os.environ['GST_DEBUG_DUMP_DOT_DIR'], "%s.dot" % name)
    log.debug(
        "Generating DOT image of pipeline '{name}' into '{file}'".format(
            name=name, file=dotfile
        )
    )
    Gst.debug_bin_to_dot_file(
        pipeline, Gst.DebugGraphDetails(int(Args.gst_debug_details)), name
    )


gst_log_messages_lastmessage = None
gst_log_messages_lastlevel = None
gst_log_messages_repeat = 0


def gst_log_messages(level):

    gstLog = logging.getLogger('Gst')

    def log(level, msg):
        if level == Gst.DebugLevel.WARNING:
            gstLog.warning(msg)
        if level == Gst.DebugLevel.FIXME:
            gstLog.warning(msg)
        elif level == Gst.DebugLevel.ERROR:
            gstLog.error(msg)
        elif level == Gst.DebugLevel.INFO:
            gstLog.info(msg)
        elif level == Gst.DebugLevel.DEBUG:
            gstLog.debug(msg)

    def logFunction(category, level, file, function, line, object, message, *user_data):
        global gst_log_messages_lastmessage, gst_log_messages_lastlevel, gst_log_messages_repeat

        msg = message.get()
        if gst_log_messages_lastmessage != msg:
            if gst_log_messages_repeat > 2:
                log(
                    gst_log_messages_lastlevel,
                    "%s [REPEATING %d TIMES]"
                    % (gst_log_messages_lastmessage, gst_log_messages_repeat),
                )

            gst_log_messages_lastmessage = msg
            gst_log_messages_repeat = 0
            gst_log_messages_lastlevel = level
            log(
                level,
                "%s: %s (in function %s() in file %s:%d)"
                % (object.name if object else "", msg, function, file, line),
            )
        else:
            gst_log_messages_repeat += 1

    Gst.debug_remove_log_function(None)
    Gst.debug_add_log_function(logFunction, None)
    Gst.debug_set_default_threshold(level)
    Gst.debug_set_active(True)
