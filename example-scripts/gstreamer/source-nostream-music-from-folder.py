#!/usr/bin/env python3
import sys, gi, signal

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject

# init GObject & Co. before importing local classes
GObject.threads_init()
Gst.init([])

class LoopSource(object):
	def __init__(self):
		pipeline = """
			audioresample name=join !
			audioconvert !
			audio/x-raw,format=S16LE,channels=2,layout=interleaved,rate=48000 !
			matroskamux !
			tcpclientsink host=localhost port=18000
		"""

		self.pipeline = Gst.parse_launch(pipeline)

		# https://c3voc.mazdermind.de/testfiles/music-snippets.tar

		self.src = Gst.ElementFactory.make('uridecodebin', None)
		self.src.set_property('uri', 'file:///home/peter/Music/pieces/001 - Bruno Mars - Grenade.mp3');
		self.src.connect('pad-added', self.on_pad_added)
		self.pipeline.add(self.src)

		self.joinpad = self.pipeline.get_by_name('join').get_static_pad('sink')

		# Binding End-of-Stream-Signal on Source-Pipeline
		self.pipeline.bus.add_signal_watch()
		self.pipeline.bus.connect("message::eos", self.on_eos)
		self.pipeline.bus.connect("message::error", self.on_error)

		print("playing")
		self.pipeline.set_state(Gst.State.PLAYING)

	def on_pad_added(self, src, pad):
		print('New Pad: '+str(pad))
		pad.add_probe(Gst.PadProbeType.EVENT_DOWNSTREAM | Gst.PadProbeType.BLOCK, self.on_pad_event)
		if self.joinpad.is_linked():
			self.joinpad.unlink(self.joinpad.get_peer())
		pad.link(self.joinpad)

	def on_pad_event(self, pad, info):
		event = info.get_event()
		print('Pad Event: '+str(event.type)+' on Pad '+str(pad))
		if event.type == Gst.EventType.EOS:
			print('Is an EOS event, dropping & unlinking')
			GObject.idle_add(self.next_track)
			return Gst.PadProbeReturn.DROP

		return Gst.PadProbeReturn.PASS

	def next_track(self):
		print("next_track")
		self.pipeline.set_state(Gst.State.READY)
		self.src.set_property('uri', 'file:///home/peter/Music/pieces/003 - Taio Cruz feat. Kylie Minogue - Higher.mp3');
		self.pipeline.set_state(Gst.State.PLAYING)
		return False

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

	src = LoopSource()

	mainloop = GObject.MainLoop()
	try:
		mainloop.run()
	except KeyboardInterrupt:
		print('Terminated via Ctrl-C')


if __name__ == '__main__':
	main()
