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
		""")
		
		uris = ('file:///home/peter/122.mp4', 'file:///home/peter/10025.mp4',)
		for idx, uri in enumerate(uris):
			# create a bin for camera input
			camberabin = Gst.parse_bin_from_description("""
				uridecodebin name=input
				input. ! videoconvert ! videoscale ! videorate ! video/x-raw,width=1024,height=576,framerate=25/1 ! identity name=video_src
				input. ! audioconvert name=audio_src
			""", False)

			# configure camera input
			camberabin.get_by_name('input').set_property('uri', uri)

			# add to pipeline and link to mixers
			self.pipeline.add(camberabin)
			camberabin.get_by_name('video_src').link(self.pipeline.get_by_name('livevideo'))
			camberabin.get_by_name('audio_src').link(self.pipeline.get_by_name('liveaudio'))

		# demonstrate some control
		liveaudio = self.pipeline.get_by_name('liveaudio')
		liveaudio.set_property('active-pad', liveaudio.get_static_pad('sink_0'))

		livevideo = self.pipeline.get_by_name('livevideo')
		pad = livevideo.get_static_pad('sink_1')
		pad.set_property('alpha', 0.5)

		self.pipeline.set_state(Gst.State.PLAYING)
