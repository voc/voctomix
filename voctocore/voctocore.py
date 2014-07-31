#!/usr/bin/python3
import gi
import signal

# import GStreamer and GTK-Helper classes
gi.require_version('Gst', '1.0')
from gi.repository import GLib, Gst, Gtk, GObject

# init GObject before importing local classes
GObject.threads_init()
Gst.init(None)

# import local classes
from videomix import Videomix
from controlserver import ControlServer

class Main:
	def __init__(self):
		# initialize subsystem
		self.videomix = Videomix()
		self.controlserver = ControlServer(self.videomix)

def runmain():
	# make killable by ctrl-c
	signal.signal(signal.SIGINT, signal.SIG_DFL)

	# start main-class and main-loop
	start=Main()
	Gtk.main()

if __name__ == '__main__':
	runmain()
