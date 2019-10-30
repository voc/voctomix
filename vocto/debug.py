#!/usr/bin/env python3
import os
import logging
from gi.repository import Gst
import gi
gi.require_version('Gst', '1.0')

log = logging.getLogger('vocto.debug')


def gst_generate_dot(pipeline, name):

    dotfile = os.path.join(os.environ['GST_DEBUG_DUMP_DOT_DIR'], "%s.dot" % name)
    log.debug("Generating DOT image of pipeline '{name}' into '{file}'".format(name=name, file=dotfile))
    Gst.debug_bin_to_dot_file(pipeline, Gst.DebugGraphDetails.CAPS_DETAILS, name)


def gst_log_messages(level):
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
    Gst.debug_set_default_threshold(level)
    Gst.debug_set_active(True)
