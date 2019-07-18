#!/usr/bin/env python3
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst
import os
import tempfile

# set GST debug dir for dot files
if not 'GST_DEBUG_DUMP_DOT_DIR' in os.environ:
    os.environ['GST_DEBUG_DUMP_DOT_DIR'] = tempfile.gettempdir()
