#!/usr/bin/python3
import sys, gi, signal

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject

# init GObject & Co. before importing local classes
GObject.threads_init()
Gst.init([])

class LoopSource(object):
	def __init__(self):
		pipeline = """
			uridecodebin name=src uri=file:///home/peter/AAA-VOC/voctomix/voctocore/scripts/bg.ts !
			video/x-raw,format=I420,width=1920,height=1080,framerate=25/1,pixel-aspect-ratio=1/1 !
			matroskamux !
			tcpclientsink host=localhost port=16000
		"""

		self.senderPipeline = Gst.parse_launch(pipeline)
		self.src = self.senderPipeline.get_by_name('src')

		# Binding End-of-Stream-Signal on Source-Pipeline
		self.senderPipeline.bus.add_signal_watch()
		self.senderPipeline.bus.connect("message::eos", self.on_eos)
		self.senderPipeline.bus.connect("message::error", self.on_error)

		print("playing")
		self.senderPipeline.set_state(Gst.State.PLAYING)


	def on_eos(self, bus, message):
		print('Received EOS-Signal, Seeking to start')
		self.src.seek(
			1.0,                 # rate (float)
			Gst.Format.TIME,     # format (Gst.Format)
			Gst.SeekFlags.FLUSH, # flags (Gst.SeekFlags)
			Gst.SeekType.SET,    # start_type (Gst.SeekType)
			0,                   # start (int)
			Gst.SeekType.NONE,   # stop_type (Gst.SeekType)
			0                    # stop (int)
		)

	def on_error(self, bus, message):
		print('Received Error-Signal')
		(error, debug) = message.parse_error()
		print('Error-Details: #%u: %s' % (error.code, debug))
		sys.exit(1)

def main():
	signal.signal(signal.SIGINT, signal.SIG_DFL)

	src = LoopSource()

	mainloop = GObject.MainLoop()
	try:
		mainloop.run()
	except KeyboardInterrupt:
		print('Terminated via Ctrl-C')


if __name__ == '__main__':
	main()
