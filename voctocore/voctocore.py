#!/usr/bin/python3
import gi
import signal

gi.require_version('Gst', '1.0')
from gi.repository import GLib, Gst, Gtk, GObject

from videomix import Videomix
from controlserver import ControlServer



class Main:
	def __init__(self):
		self.videomix = Videomix()
		self.controlserver = ControlServer(self.videomix)

def runmain():
	GObject.threads_init()
	Gst.init(None)

	signal.signal(signal.SIGINT, signal.SIG_DFL)
	start=Main()
	Gtk.main()

if __name__ == '__main__':
	runmain()
