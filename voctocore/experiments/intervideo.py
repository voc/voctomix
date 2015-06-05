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
		self.source_pipeline = None

		self.sink_pipeline = Gst.parse_launch("""
			intervideosrc channel=video !
				queue !
				video/x-raw,width=800,height=450,format=I420,framerate=25/1 !
				textoverlay halignment=left valignment=top ypad=50 text=intervideosrc !
				timeoverlay halignment=left valignment=top ypad=50 xpad=400 !
				tee name=vtee

			interaudiosrc blocksize=4096 channel=audio !
				queue !
				audio/x-raw,format=S16LE,layout=interleaved,rate=48000,channels=2 !
				tee name=atee


			vtee. !
				queue !
				videoconvert !
				textoverlay halignment=left valignment=top ypad=75 text=avenc_mpeg2video !
				timeoverlay halignment=left valignment=top ypad=75 xpad=400 !
				avenc_mpeg2video bitrate=50000 max-key-interval=0 !
				queue !
				mux.

			atee. !
				queue !
				avenc_mp2 bitrate=192000 !
				queue !
				mux.

			mpegtsmux name=mux !
				filesink location=foo.ts


			vtee. !
				queue !
				textoverlay halignment=left valignment=top ypad=75 text=xvimagesink !
				timeoverlay halignment=left valignment=top ypad=75 xpad=400 !
				videoconvert !
				xvimagesink

			atee. !
				queue !
				audioconvert !
				alsasink
		""")

		# Create the server, binding to localhost on port 5000
		sock = socket.socket(socket.AF_INET6)
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, False)
		sock.bind(('::', 10000))
		sock.listen(1)

		# register socket for callback inside the GTK-Mainloop
		GObject.io_add_watch(sock, GObject.IO_IN, self.on_connect)


	def on_connect(self, sock, *args):
		'''Asynchronous connection listener. Starts a handler for each connection.'''
		if self.source_pipeline:
			return False

		conn, addr = sock.accept()
		print("Connection from", addr)

		self.source_pipeline = Gst.parse_launch("""
			fdsrc name=a fd=%u !
				matroskademux name=demux

			demux. !
				video/x-raw,width=800,height=450,format=I420,framerate=25/1 !
				queue !
				textoverlay halignment=left valignment=top ypad=25 text=intervideosink !
				timeoverlay halignment=left valignment=top ypad=25 xpad=400 !
				intervideosink channel=video

			demux. !
				audio/x-raw,format=S16LE,channels=2,layout=interleaved,rate=48000,channel-mask=(bitmask)0x3 !
				queue !
				interaudiosink channel=audio

		""" % conn.fileno())

		self.source_pipeline.bus.add_signal_watch()
		self.source_pipeline.bus.connect("message::eos", self.on_disconnect)

		self.source_pipeline.set_state(Gst.State.PLAYING)

		self.conn = conn
		return True

	def on_disconnect(self, bus, message):
		self.source_pipeline.set_state(Gst.State.NULL)
		self.source_pipeline = None
		self.conn = None
		return True

	def run(self):
		self.sink_pipeline.set_state(Gst.State.PLAYING)
		self.mainloop.run()

example = Example()
example.run()
