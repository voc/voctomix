import sys, inspect
from pprint import pprint
from gi.repository import GLib, Gst

class Videomix:
	decoder = []
	mixerpads = []

	def __init__(self):
		self.pipeline = Gst.parse_launch("""
			videomixer name=livevideo ! autovideosink
			input-selector name=liveaudio ! autoaudiosink
			
			uridecodebin name=cam0 uri=file:///home/peter/122.mp4
			uridecodebin name=cam1 uri=file:///home/peter/10025.mp4
			
			cam0. ! videoconvert ! videoscale ! videorate ! video/x-raw,width=1024,height=576,framerate=25/1 ! livevideo.
			cam1. ! videoconvert ! videoscale ! videorate ! video/x-raw,width=1024,height=576,framerate=25/1 ! livevideo.
			
			cam0. ! audioconvert ! liveaudio.
			cam1. ! audioconvert ! liveaudio.
		""")
		
		liveaudio = self.pipeline.get_by_name('liveaudio')
		liveaudio.set_property('active-pad', liveaudio.get_static_pad('sink_0'))

		livevideo = self.pipeline.get_by_name('livevideo')
		pad = livevideo.get_static_pad('sink_1')
		pad.set_property('alpha', 0.5)

		self.pipeline.set_state(Gst.State.PLAYING)
