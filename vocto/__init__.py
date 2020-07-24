#!/usr/bin/env python3
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst
import os

# set GST debug dir for dot files
if not 'GST_DEBUG_DUMP_DOT_DIR' in os.environ:
    os.environ['GST_DEBUG_DUMP_DOT_DIR'] = os.getcwd()

def kind_has_audio(source):
    return source in ["decklink", "tcp", "test", "pa"]

def kind_has_video(source):
    return source in ["decklink", "tcp", "test", "v4l2", "img", "file", "background", "RPICam"]
