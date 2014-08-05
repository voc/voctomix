#!/usr/bin/python3
import gi
import signal
from termcolor import colored

# import GStreamer and GTK-Helper classes
gi.require_version('Gst', '1.0')
from gi.repository import GLib, Gst, Gtk, GObject

# init GObject before importing local classes
GObject.threads_init()
Gst.init(None)
loop = GLib.MainLoop()

def busfunc(bus, message):
	print(colored(message.src.get_name(), 'green'), message.type, message)
	if message.type == Gst.MessageType.ERROR:
		(err, debug) = message.parse_error()
		print(colored(err, 'red'))
		print(colored(debug, 'yellow'))
		
		if message.src.get_name() == 'http':
			failover = p.get_by_name('failover')
			failover.set_property('active-pad', failover.get_static_pad('sink_1'))

# make killable by ctrl-c
signal.signal(signal.SIGINT, signal.SIG_DFL)

print("parse_launch")
p = Gst.parse_launch("""
	input-selector name=failover ! autovideosink

	videotestsrc ! video/x-raw,width=1280,height=720 ! failover.sink_1
	souphttpsrc name=http location="http://localhost/~peter/ED_1280.avi" ! decodebin ! failover.sink_0
""")

print("add_watch")
bus = p.get_bus()
bus.add_signal_watch()
bus.connect('message', busfunc)

# print("add_watch")
# httpbus = p.get_by_name('http').get_bus()
# httpbus.add_watch(0, busfunc, None)

print("set_state(PLAYING)")
p.set_state(Gst.State.PLAYING)

loop.run()
