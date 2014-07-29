import sys, inspect, math
from pprint import pprint
from gi.repository import GLib, Gst

class Videomix:
	decoder = []
	mixerpads = []

	def __init__(self):
		self.pipeline = Gst.Pipeline()

		# create audio and video mixer
		mixerbin = self.createMixer()

		# collection of video-sources to connect to the quadmix
		quadmixSources = []

		# create camera sources
		for camberabin in self.createDummyCamSources():
			# link camerasource to audiomixer
			camberabin.get_by_name('audio_src').link(self.pipeline.get_by_name('liveaudio'))

			# inject a ×2 distributor and link one end to the live-mixer
			distributor = self.createDistributor(camberabin.get_by_name('video_src'))
			distributor.get_by_name('a').link(self.pipeline.get_by_name('livevideo'))

			# collect the other end to add it later to the quadmix
			quadmixSources.append(distributor.get_by_name('b'))

		# would generate pause & slides with another generator which only
		# yields if the respective fil are there and which only have a video-pad

		self.addVideosToQuadmix(quadmixSources, self.pipeline.get_by_name('quadmix'))

		# demonstrate some control
		liveaudio = self.pipeline.get_by_name('liveaudio')
		liveaudio.set_property('active-pad', liveaudio.get_static_pad('sink_0'))

		livevideo = self.pipeline.get_by_name('livevideo')
		pad = livevideo.get_static_pad('sink_1')
		pad.set_property('alpha', 0.5)

		self.pipeline.set_state(Gst.State.PLAYING)

	def createMixer(self):
		mixerbin = Gst.parse_bin_from_description("""
			videomixer name=livevideo ! autovideosink
			input-selector name=liveaudio ! autoaudiosink

			videomixer name=quadmix ! autovideosink
		""", False)
		self.pipeline.add(mixerbin)
		return mixerbin

	def addVideosToQuadmix(self, videosources, quadmix):
		count = len(videosources)
		rows = math.ceil(math.sqrt(count))
		cols = math.ceil(count / rows)
		for videosource in videosources:
			# define size somewhere, scale and place here
			videosource.link(quadmix)

	def createDistributor(self, videosource):
		distributor = Gst.parse_bin_from_description("""
			tee name=t
			t. ! queue name=a
			t. ! queue name=b
		""", False)

		self.pipeline.add(distributor)
		videosource.link(distributor.get_by_name('t'))
		return distributor

	def createDummyCamSources(self):
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

			# pass bin upstream
			self.pipeline.add(camberabin)
			yield camberabin



	def createCamSources(self):
		for cam in range(2):
			# create a bin for camera input
			camberabin = Gst.parse_bin_from_description("""
				decklinksrc name=input input=sdi input-mode=1080p25
				input. ! videoconvert ! videoscale ! videorate ! video/x-raw,width=1920,height=1080,framerate=25/1 ! identity name=video_src
				input. ! audioconvert name=audio_src
			""", False)

			# configure camera input
			camberabin.get_by_name('input').set_property('subdevice', cam)

			# pass bin upstream
			self.pipeline.add(camberabin)
			yield camberabin
