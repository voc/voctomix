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
