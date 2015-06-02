#!/usr/bin/python3
import gi, time
import socket

# import GStreamer and GTK-Helper classes
gi.require_version('Gst', '1.0')
from gi.repository import GLib, Gst, GObject

# init GObject before importing local classes
GObject.threads_init()
Gst.init(None)

class Example:
	def __init__(self):
		self.mainloop = GObject.MainLoop()

		self.src   = Gst.parse_launch("""
			tcpserversrc port=10000 !
			matroskademux name=demux

			demux. !
			audio/x-raw,format=S16LE,channels=2,layout=interleaved,rate=48000,channel-mask=(bitmask)0x3 !
			queue !
			tee name=atee

			atee. ! queue ! interaudiosink channel=audio_cam1_mixer
			atee. ! queue ! interaudiosink channel=audio_cam1_mirror

			demux. !
			video/x-raw,format=I420,width=800,height=450,framerate=25/1 !
			queue !
			tee name=vtee

			vtee. ! queue ! intervideosink channel=video_cam1_mixer
			vtee. ! queue ! intervideosink channel=video_cam1_mirror
		""")

		self.sink   = Gst.parse_launch("""
			interaudiosrc channel=audio_cam1_mirror !
			audio/x-raw,format=S16LE,channels=2,layout=interleaved,rate=48000,channel-mask=(bitmask)0x3 !
			queue !
			mux.

			intervideosrc channel=video_cam1_mirror !
			video/x-raw,format=I420,width=800,height=450,framerate=25/1 !
			queue !
			mux.

			matroskamux
				name=mux
				streamable=true
				writing-app=Voctomix-AVRawOutput !

			tcpserversink port=11000
		""")

	def run(self):
		self.src.set_state(Gst.State.PLAYING)
		self.sink.set_state(Gst.State.PLAYING)
		self.mainloop.run()


example = Example()
example.run()
