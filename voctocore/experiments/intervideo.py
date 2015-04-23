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
		self.vsink   = Gst.parse_launch('intervideosrc channel=video ! video/x-raw,height=600,width=800,format=I420,framerate=25/1 ! timeoverlay ! videoconvert ! ximagesink')
		self.vsource = None

		self.asink   = Gst.parse_launch('interaudiosrc channel=audio ! audio/x-raw,format=S16LE,layout=interleaved,rate=48000,channels=2 ! autoaudiosink')
		self.asource = None


		# Create the server, binding to localhost on port 5000
		vsock = socket.socket(socket.AF_INET6)
		vsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		vsock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, False)
		vsock.bind(('::', 5000))
		vsock.listen(1)

		# register socket for callback inside the GTK-Mainloop
		GObject.io_add_watch(vsock, GObject.IO_IN, self.connection_handler_video)



		# Create the server, binding to localhost on port 6000
		asock = socket.socket(socket.AF_INET6)
		asock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		asock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, False)
		asock.bind(('::', 6000))
		asock.listen(1)

		# register socket for callback inside the GTK-Mainloop
		GObject.io_add_watch(asock, GObject.IO_IN, self.connection_handler_audio)



	def connection_handler_video(self, sock, *args):
		'''Asynchronous connection listener. Starts a handler for each connection.'''
		if self.vsource:
			return False

		conn, addr = sock.accept()
		print("Connection from", addr)

		self.vsource = Gst.parse_launch('appsrc name=a ! gdpdepay ! video/x-raw,height=600,width=800,format=I420,framerate=25/1 ! timeoverlay halignment=right ! intervideosink channel=video')
		self.vsource.set_state(Gst.State.PLAYING)

		# register data-received handler inside the GTK-Mainloop
		GObject.io_add_watch(conn, GObject.IO_IN, self.data_handler_video)
		return True

	def data_handler_video(self, conn, *args):
		'''Asynchronous data handler. Processes data-blocks line from the socket.'''
		blob = conn.recv(10000000) # >1920x1080x3
		if not len(blob):
			print("Connection closed.")
			self.vsource.set_state(Gst.State.NULL)
			self.vsource = None
			return False

		print("Video-Blob of %u bytes" % len(blob))
		buf = Gst.Buffer.new_wrapped(blob)
		self.vsource.get_by_name('a').emit('push-buffer', buf)
		return True



	def connection_handler_audio(self, sock, *args):
		'''Asynchronous connection listener. Starts a handler for each connection.'''
		if self.asource:
			return False

		conn, addr = sock.accept()
		print("Connection from", addr)

		self.asource = Gst.parse_launch('appsrc name=a ! gdpdepay ! audio/x-raw,format=S16LE,layout=interleaved,rate=48000,channels=2 ! interaudiosink channel=audio')
		self.asource.set_state(Gst.State.PLAYING)

		# register data-received handler inside the GTK-Mainloop
		GObject.io_add_watch(conn, GObject.IO_IN, self.data_handler_audio)
		return True

	def data_handler_audio(self, conn, *args):
		'''Asynchronous data handler. Processes data-blocks line from the socket.'''
		blob = conn.recv(10000000) # >1920x1080x3
		if not len(blob):
			print("Connection closed.")
			self.asource.set_state(Gst.State.NULL)
			self.asource = None
			return False

		print("Audio-Blob of %u bytes" % len(blob))
		buf = Gst.Buffer.new_wrapped(blob)
		self.asource.get_by_name('a').emit('push-buffer', buf)
		return True



	def run(self):
		self.vsink.set_state(Gst.State.PLAYING)
		self.asink.set_state(Gst.State.PLAYING)
		self.mainloop.run()

	def kill(self):
		self.vsink.set_state(Gst.State.NULL)
		self.asink.set_state(Gst.State.NULL)
		self.mainloop.quit()

	def on_eos(self, bus, msg):
		print('on_eos()')
		#self.kill()

	def on_error(self, bus, msg):
		print('on_error():', msg.parse_error())
		#self.kill()

example = Example()
example.run()
