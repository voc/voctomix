#!/usr/bin/python3
import sys, gi, signal

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GstNet, GObject

# init GObject & Co. before importing local classes
GObject.threads_init()
Gst.init([])

class Source(object):
	def __init__(self):
		# it works much better with a local file
		pipeline = """
			videotestsrc pattern=ball foreground-color=0x00ff0000 background-color=0x00440000 !
				timeoverlay !
				video/x-raw,format=I420,width=192,height=108,framerate=25/1,pixel-aspect-ratio=1/1 !
				mux.

			audiotestsrc freq=330 !
				audio/x-raw,format=S16LE,channels=2,layout=interleaved,rate=48000 !
				mux.

			matroskamux name=mux !
				tcpclientsink host=127.0.0.1 port=10000
		"""

		clock = Gst.SystemClock.obtain()
		self.clock = GstNet.NetClientClock.new('voctocore', '127.0.0.1', 9998, clock.get_time())
		print('obtained NetClientClock from host', self.clock)

		self.senderPipeline = Gst.parse_launch(pipeline)
		self.senderPipeline.use_clock(self.clock)
		self.src = self.senderPipeline.get_by_name('src')

		# Binding End-of-Stream-Signal on Source-Pipeline
		self.senderPipeline.bus.add_signal_watch()
		self.senderPipeline.bus.connect("message::eos", self.on_eos)
		self.senderPipeline.bus.connect("message::error", self.on_error)

		print("playing")
		self.senderPipeline.set_state(Gst.State.PLAYING)


	def on_eos(self, bus, message):
		print('Received EOS-Signal')
		sys.exit(1)

	def on_error(self, bus, message):
		print('Received Error-Signal')
		(error, debug) = message.parse_error()
		print('Error-Details: #%u: %s' % (error.code, debug))
		sys.exit(1)

def main():
	signal.signal(signal.SIGINT, signal.SIG_DFL)

	src = Source()

	mainloop = GObject.MainLoop()
	try:
		mainloop.run()
	except KeyboardInterrupt:
		print('Terminated via Ctrl-C')


if __name__ == '__main__':
	main()
