import sys, inspect, math
from pprint import pprint
from gi.repository import GLib, Gst

class Videomix:
	decoder = []
	mixerpads = []
	monitorSize = (1024, 576)

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
			distributor = self.createDistributor(camberabin.get_by_name('video_src'), camberabin.get_name())
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

		Gst.debug_bin_to_dot_file(self.pipeline, Gst.DebugGraphDetails.ALL, 'test')
		self.pipeline.set_state(Gst.State.PLAYING)

	def createMixer(self):
		mixerbin = Gst.parse_bin_from_description("""
			videomixer name=livevideo ! autovideosink
			input-selector name=liveaudio ! autoaudiosink

			videotestsrc pattern="solid-color" foreground-color=0x808080 ! capsfilter name=filter ! videomixer name=quadmix ! autovideosink
		""", False)

		quadmixcaps = Gst.Caps.new_empty_simple('video/x-raw')
		quadmixcaps.set_value('width', round(self.monitorSize[0]))
		quadmixcaps.set_value('height', round(self.monitorSize[1]))
		mixerbin.get_by_name('filter').set_property('caps', quadmixcaps)

		mixerbin.set_name('mixerbin')
		self.pipeline.add(mixerbin)
		return mixerbin

	def addVideosToQuadmix(self, videosources, quadmix):
		count = len(videosources)
		place = [0, 0]
		grid = [0, 0]
		grid[0] = math.ceil(math.sqrt(count))
		grid[1] = math.ceil(count / grid[0])

		cellSize = (self.monitorSize[0] / grid[0], self.monitorSize[1] / grid[1])
		print("showing {} videosources in a {}×{} grid in a {}×{} px window, which gives cells of {}×{} px per videosource".format(
			count, grid[0], grid[1], self.monitorSize[0], self.monitorSize[1], cellSize[0], cellSize[1]))
		
		for idx, videosource in enumerate(videosources):
			caps = videosource.get_static_pad('src').query_caps(None)
			capsstruct = caps.get_structure(0)
			srcSize = (
				capsstruct.get_int('width')[1],
				capsstruct.get_int('height')[1],
			)

			f = max(srcSize[0] / cellSize[0], srcSize[1] / cellSize[1])
			scaleSize = (
				srcSize[0] / f,
				srcSize[1] / f,
			)

			coord = (
				place[0] * cellSize[0] + (cellSize[0] - scaleSize[0]) / 2,
				place[1] * cellSize[1] + (cellSize[1] - scaleSize[1]) / 2,
			)

			print("placing videosrc {} of size {}×{} scaled by {} to {}×{} in a cell {}×{} px cell ({}/{}) at position ({}/{})".format(
				idx, srcSize[0], srcSize[1], f, scaleSize[0], scaleSize[1], cellSize[0], cellSize[1], place[0], place[1], coord[0], coord[1]))

			scalecaps = Gst.Caps.new_empty_simple('video/x-raw')
			scalecaps.set_value('width', round(scaleSize[0]))
			scalecaps.set_value('height', round(scaleSize[1]))

			scaler = Gst.ElementFactory.make('videoscale', 'quadmix-scaler({})'.format(idx))
			self.pipeline.add(scaler)
			videosource.link(scaler)

			# define size somewhere, scale and place here
			sinkpad = quadmix.get_request_pad('sink_%u')
			sinkpad.set_property('xpos', round(coord[0]))
			sinkpad.set_property('ypos', round(coord[1]))
			scaler.link_filtered(quadmix, scalecaps)

			place[0] += 1
			if place[0] >= grid[0]:
				place[1] += 1
				place[0] = 0

	def createDistributor(self, videosource, name):
		distributor = Gst.parse_bin_from_description("""
			tee name=t
			t. ! queue name=a
			t. ! queue name=b
		""", False)
		distributor.set_name('distributor({0})'.format(name))

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
			camberabin.set_name('dummy-camberabin({0})'.format(uri))

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
			camberabin.set_name('camberabin({0})'.format(cam))

			# configure camera input
			camberabin.get_by_name('input').set_property('subdevice', cam)

			# pass bin upstream
			self.pipeline.add(camberabin)
			yield camberabin
