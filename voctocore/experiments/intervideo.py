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
		#self.vsink   = Gst.parse_launch('intervideosrc channel=video ! video/x-raw,height=600,width=800,format=I420,framerate=25/1 ! timeoverlay ! videoconvert ! ximagesink')
		self.vsource = None

		#self.asink   = Gst.parse_launch('interaudiosrc channel=audio ! audio/x-raw,format=S16LE,layout=interleaved,rate=48000,channels=2 ! autoaudiosink')
		self.asource = None

		self.sink   = Gst.parse_launch("""
			intervideosrc channel=video !
				queue !
				video/x-raw,height=600,width=800,format=I420,framerate=25/1 !
				timeoverlay !
				tee name=vtee !
				queue !
				videoconvert !
				avenc_mpeg2video bitrate=50000 max-key-interval=0 !
				queue !
				mux.

			interaudiosrc blocksize=4096 channel=audio !
				queue !
				audio/x-raw,format=S16LE,layout=interleaved,rate=48000,channels=2 !
				tee name=atee !
				queue !
				avenc_mp2 bitrate=192000 !
				queue !
				mux.

			mpegtsmux name=mux !
				filesink location=foo.ts

			vtee. ! queue ! videoconvert ! xvimagesink
			atee. ! queue ! audioconvert ! alsasink
		""")


		# Create the server, binding to localhost on port 5000
		vsock = socket.socket(socket.AF_INET6)
		vsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		vsock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, False)
		vsock.bind(('::', 5000))
		vsock.listen(1)


		# Create the server, binding to localhost on port 5000
		asock = socket.socket(socket.AF_INET6)
		asock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		asock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, False)
		asock.bind(('::', 6000))
		asock.listen(1)

		# register socket for callback inside the GTK-Mainloop
		GObject.io_add_watch(vsock, GObject.IO_IN, self.video_connect)
		GObject.io_add_watch(asock, GObject.IO_IN, self.audio_connect)


	def video_connect(self, sock, *args):
		'''Asynchronous connection listener. Starts a handler for each connection.'''
		if self.vsource:
			return False

		conn, addr = sock.accept()
		print("Connection from", addr)

		self.vsource = Gst.parse_launch('fdsrc name=a fd=%u ! gdpdepay ! video/x-raw,height=600,width=800,format=I420,framerate=25/1 ! timeoverlay halignment=right ! intervideosink channel=video' % conn.fileno())

		self.vsource.bus.add_signal_watch()
		self.vsource.bus.connect("message::eos", self.video_disconnect)

		self.vsource.set_state(Gst.State.PLAYING)

		self.vconn = conn
		return True

	def video_disconnect(self, bus, message):
		self.vsource.set_state(Gst.State.NULL)
		self.vsource = None
		self.vconn = None
		return True


	def audio_connect(self, sock, *args):
		'''Asynchronous connection listener. Starts a handler for each connection.'''
		if self.asource:
			return False

		conn, addr = sock.accept()
		print("Connection from", addr)

		self.asource = Gst.parse_launch('fdsrc name=a fd=%u ! gdpdepay ! audio/x-raw,format=S16LE,layout=interleaved,rate=48000,channels=2 ! interaudiosink channel=audio' % conn.fileno())

		self.asource.bus.add_signal_watch()
		self.asource.bus.connect("message::eos", self.audio_disconnect)

		self.asource.set_state(Gst.State.PLAYING)

		self.aconn = conn
		return True

	def audio_disconnect(self, bus, message):
		self.asource.set_state(Gst.State.NULL)
		self.asource = None
		self.aconn = None
		return True


	def run(self):
		self.sink.set_state(Gst.State.PLAYING)
		self.mainloop.run()

	def kill(self):
		self.sink.set_state(Gst.State.NULL)
		self.mainloop.quit()

example = Example()
example.run()
