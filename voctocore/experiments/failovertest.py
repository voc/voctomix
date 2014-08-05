#!/usr/bin/python3
import gi
import time
import signal
from http.client import HTTPConnection
from termcolor import colored
from threading import Timer, Thread

# import GStreamer and GTK-Helper classes
gi.require_version('Gst', '1.0')
from gi.repository import GLib, Gst, Gtk, GObject

# init GObject before importing local classes
GObject.threads_init()
Gst.init(None)
loop = GLib.MainLoop()

# make killable by ctrl-c
signal.signal(signal.SIGINT, signal.SIG_DFL)

# parse_launch
p = Gst.parse_launch("""
	input-selector name=failover ! autovideosink

	appsrc name=src blocksize=4096 is-live=true block=true ! multipartdemux name=demux ! jpegparse ! jpegdec ! videoconvert ! failover.sink_1
	videotestsrc ! video/x-raw,width=500,height=375 ! failover.sink_0
""")

def failsafeVideoSource():
	src = p.get_by_name('src')
	dec = p.get_by_name('dec')
	demux = p.get_by_name('demux')
	failover = p.get_by_name('failover')
	srcActive = True

	while True:
		print('connecting to framegrabber')
		try:
			con = HTTPConnection('beachcam.kdhnc.com', 80, timeout=3)
			req = con.request('GET', '/mjpg/video.mjpg?camera=1')
			res = con.getresponse()
			srcActive = True

			print('connected, switching to video')
			failover.set_property('active-pad', failover.get_static_pad('sink_1'))

			while srcActive:
				chunk = res.read(4094)
				chunklen = len(chunk)
				print('read ', len(chunk), ' of ', 4096, ', closed=', res.isclosed())
				
				if chunklen > 0:
					src.emit('push-buffer', Gst.Buffer.new_wrapped(chunk))
				else:
					srcActive = False
		except:
			print('exception')
			srcActive = False

		print('switching to failsave')
		failover.set_property('active-pad', failover.get_static_pad('sink_0'))

		print('sleeping before retry')
		time.sleep(1)

fsThread = Thread(target=failsafeVideoSource)
fsThread.deamon = True
fsThread.start()

# set playing
p.set_state(Gst.State.PLAYING)

# start mainloop
loop.run()
