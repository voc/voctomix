#!/usr/bin/env python3
import os
import logging
from gi.repository import Gst
import gi
gi.require_version('Gst', '1.0')

log = logging.getLogger('vocto.debug')


def gst_generate_png(pipeline, name):
    dotfile = os.path.join(os.environ['GST_DEBUG_DUMP_DOT_DIR'], "%s.dot" % name)
    pngfile = os.path.join(os.getcwd(), "%s.dot.png" % name)
    log.debug("Generating PNG image of pipeline '{name}' into '{file}'".format(name=name, file=pngfile))
    Gst.debug_bin_to_dot_file(pipeline, 0, name)
    os.system("dot -Tpng -o{pngfile} {dotfile}".format(pngfile=pngfile,dotfile=dotfile))
    os.system("rm {dotfile}".format(pngfile=pngfile,dotfile=dotfile))
