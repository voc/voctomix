import sys, inspect, math
from pprint import pprint
from gi.repository import GLib, Gst
from controlserver import controlServerEntrypoint

class Videomix:
"""mixing, streaming and encoding pipeline constuction and control"""
	# size of the monitor-streams
	# should be anamorphic PAL, beacuse we encode it to dv and send it to the mixer-gui
	monitorSize = (1024, 576)

	def __init__(self):
		"""initialize video mixing, streaming and encoding pipeline"""
		# initialize an empty pipeline
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

		# TODO: generate pause & slides with another generator here which only
		# yields if the respective files are present and which only have a video-pad

		# add all video-sources to the quadmix-monitor-screen
		self.addVideosToQuadmix(quadmixSources, self.pipeline.get_by_name('quadmix'))

		Gst.debug_bin_to_dot_file(self.pipeline, Gst.DebugGraphDetails.ALL, 'test')
		self.pipeline.set_state(Gst.State.PLAYING)

	def createMixer(self):
		"""create audio and video mixer"""
		# create mixer-pipeline from string
		mixerbin = Gst.parse_bin_from_description("""
			videomixer name=livevideo ! autovideosink
			input-selector name=liveaudio ! autoaudiosink

			videotestsrc pattern="solid-color" foreground-color=0x808080 ! capsfilter name=filter ! videomixer name=quadmix ! autovideosink
		""", False)

		# define caps for the videotestsrc which generates the background-color for the quadmix
		bgcaps = Gst.Caps.new_empty_simple('video/x-raw')
		bgcaps.set_value('width', round(self.monitorSize[0]))
		bgcaps.set_value('height', round(self.monitorSize[1]))
		mixerbin.get_by_name('filter').set_property('caps', bgcaps)

		# name the bin, add and return it
		mixerbin.set_name('mixerbin')
		self.pipeline.add(mixerbin)
		return mixerbin

	def addVideosToQuadmix(self, videosources, quadmix):
		"""add all avaiable videosources to the quadmix"""
		count = len(videosources)

		# coordinate of the cell where we place the next video
		place = [0, 0]
		
		# number of cells in the quadmix-monitor
		grid = [0, 0]
		grid[0] = math.ceil(math.sqrt(count))
		grid[1] = math.ceil(count / grid[0])

		# size of each cell in the quadmix-monitor
		cellSize = (
			self.monitorSize[0] / grid[0],
			self.monitorSize[1] / grid[1]
		)

		print("showing {} videosources in a {}×{} grid in a {}×{} px window, which gives cells of {}×{} px per videosource".format(
			count, grid[0], grid[1], self.monitorSize[0], self.monitorSize[1], cellSize[0], cellSize[1]))

		# iterate over all video-sources
		for idx, videosource in enumerate(videosources):
			# generate a pipeline for this videosource which
			# - scales the video to the request
			# - remove n px of the video (n = 5 if the video is highlighted else 0)
			# - add a colored border of n px of the video (n = 5 if the video is highlighted else 0)
			# - overlay the index of the video as text in the top left corner
			# - known & named output
			previewbin = Gst.parse_bin_from_description("""
				videoscale name=in !
				capsfilter name=caps !
				videobox name=crop top=0 left=0 bottom=0 right=0 !
				videobox fill=red top=-0 left=-0 bottom=-0 right=-0 name=add !
				textoverlay color=0xFFFFFFFF halignment=left valignment=top xpad=10 ypad=5 font-desc="sans 35" name=text !
				identity name=out
			""", False)

			# name the bin and add it
			self.pipeline.add(previewbin)
			previewbin.set_name('previewbin-{}'.format(idx))

			# set the overlay-text
			previewbin.get_by_name('text').set_property('text', str(idx))

			# query the video-source caps and extract its size
			caps = videosource.get_static_pad('src').query_caps(None)
			capsstruct = caps.get_structure(0)
			srcSize = (
				capsstruct.get_int('width')[1],
				capsstruct.get_int('height')[1],
			)

			# calculate the ideal scale factor and scale the sizes
			f = max(srcSize[0] / cellSize[0], srcSize[1] / cellSize[1])
			scaleSize = (
				srcSize[0] / f,
				srcSize[1] / f,
			)

			# calculate the top/left coordinate
			coord = (
				place[0] * cellSize[0] + (cellSize[0] - scaleSize[0]) / 2,
				place[1] * cellSize[1] + (cellSize[1] - scaleSize[1]) / 2,
			)

			print("placing videosource {} of size {}×{} scaled by {} to {}×{} in a cell {}×{} px cell ({}/{}) at position ({}/{})".format(
				idx, srcSize[0], srcSize[1], f, scaleSize[0], scaleSize[1], cellSize[0], cellSize[1], place[0], place[1], coord[0], coord[1]))

			# link the videosource to the input of the preview-bin
			videosource.link(previewbin.get_by_name('in'))

			# create and set the caps for the preview-scaler
			scalecaps = Gst.Caps.new_empty_simple('video/x-raw')
			scalecaps.set_value('width', round(scaleSize[0]))
			scalecaps.set_value('height', round(scaleSize[1]))
			previewbin.get_by_name('caps').set_property('caps', scalecaps)

			# request a pad from the quadmixer and configure x/y position
			sinkpad = quadmix.get_request_pad('sink_%u')
			sinkpad.set_property('xpos', round(coord[0]))
			sinkpad.set_property('ypos', round(coord[1]))

			# link the output of the preview-bin to the mixer
			previewbin.get_by_name('out').link(quadmix)

			# increment grid position
			place[0] += 1
			if place[0] >= grid[0]:
				place[1] += 1
				place[0] = 0

	def createDistributor(self, videosource, name):
		"""create a simple ×2 distributor"""
		distributor = Gst.parse_bin_from_description("""
			tee name=t
			t. ! queue name=a
			t. ! queue name=b
		""", False)

		# set a name and add to pipeline
		distributor.set_name('distributor({0})'.format(name))
		self.pipeline.add(distributor)

		# link input to the tee
		videosource.link(distributor.get_by_name('t'))
		return distributor

	def createDummyCamSources(self):
		"""create test-video-sources from files or urls"""

		# TODO make configurable
		uris = ('file:///home/peter/122.mp4', 'file:///home/peter/10025.mp4',)
		for idx, uri in enumerate(uris):
			# create a bin for a simulated camera input
			# force the input resolution to 1024x576 because that way the following elements
			# in the pipeline cam know the size even if the file is not yet loaded. the quadmixer
			# is not resize-capable
			camberabin = Gst.parse_bin_from_description("""
				uridecodebin name=input
				input. ! videoconvert ! videoscale ! videorate ! video/x-raw,width=1024,height=576,framerate=25/1 ! identity name=video_src
				input. ! audioconvert name=audio_src
			""", False)

			# set name and uri
			camberabin.set_name('dummy-camberabin({0})'.format(uri))
			camberabin.get_by_name('input').set_property('uri', uri)

			# add to pipeline and pass the bin upstream
			self.pipeline.add(camberabin)
			yield camberabin


	def createCamSources(self):
		"""create real-video-sources from the bmd-drivers"""

		# TODO make number of installed cams configurable
		for cam in range(2):
			# create a bin for camera input
			camberabin = Gst.parse_bin_from_description("""
				decklinksrc name=input input=sdi input-mode=1080p25
				input. ! videoconvert ! videoscale ! videorate ! video/x-raw,width=1920,height=1080,framerate=25/1 ! identity name=video_src
				input. ! audioconvert name=audio_src
			""", False)

			# set name and subdevice
			camberabin.set_name('camberabin({0})'.format(cam))
			camberabin.get_by_name('input').set_property('subdevice', cam)

			# add to pipeline and pass the bin upstream
			self.pipeline.add(camberabin)
			yield camberabin

	def iteratorHelper(self, it):
		while True:
			result, value = it.next()
			if result == Gst.IteratorResult.DONE:
				break

			if result != Gst.IteratorResult.OK:
				raise IteratorError(result)

			yield value

	### below are access-methods for the ControlServer

	@controlServerEntrypoint
	def numAudioSources(self):
		"""return number of available audio sources"""
		liveaudio = self.pipeline.get_by_name('liveaudio')
		return str(len(list(self.iteratorHelper(liveaudio.iterate_sink_pads()))))


	@controlServerEntrypoint
	def switchAudio(self, audiosource):
		"""switch audio to the selected audio"""
		liveaudio = self.pipeline.get_by_name('liveaudio')
		pad = liveaudio.get_static_pad('sink_{}'.format(audiosource))
		if pad is None:
			return 'unknown audio-source: {}'.format(audiosource)

		liveaudio.set_property('active-pad', pad)
		return True


	@controlServerEntrypoint
	def numVideoSources(self):
		"""return number of available video sources"""
		livevideo = self.pipeline.get_by_name('livevideo')
		return str(len(list(self.iteratorHelper(livevideo.iterate_sink_pads()))))


	@controlServerEntrypoint
	def switchVideo(self, videosource):
		"""switch audio to the selected video"""
		livevideo = self.pipeline.get_by_name('livevideo')
		pad = livevideo.get_static_pad('sink_{}'.format(videosource))
		if pad is None:
			return 'unknown video-source: {}'.format(videosource)

		pad.set_property('alpha', 1)
		for iterpad in self.iteratorHelper(livevideo.iterate_sink_pads()):
			if pad != iterpad:
				iterpad.set_property('alpha', 0)


	@controlServerEntrypoint
	def fadeVideo(self, videosource):
		"""fade video to the selected video"""
		raise NotImplementedError("fade command is not implemented yet")


	@controlServerEntrypoint
	def setPipVideo(self, videosource):
		"""switch video-source in the PIP to the selected video"""
		raise NotImplementedError("pip commands are not implemented yet")


	@controlServerEntrypoint
	def fadePipVideo(self, videosource):
		"""fade video-source in the PIP to the selected video"""
		raise NotImplementedError("pip commands are not implemented yet")


	class PipPlacements:
		"""enumeration of possible PIP-Placements"""
		TopLeft, TopRight, BottomLeft, BottomRight = range(4)


	@controlServerEntrypoint
	def setPipPlacement(self, placement):
		"""place PIP in the selected position"""
		assert(isinstance(placement, PipPlacements))
		raise NotImplementedError("pip commands are not implemented yet")


	@controlServerEntrypoint
	def setPipStatus(self, enabled):
		"""show or hide PIP"""
		raise NotImplementedError("pip commands are not implemented yet")


	@controlServerEntrypoint
	def fadePipStatus(self, enabled):
		"""fade PIP in our out"""
		raise NotImplementedError("pip commands are not implemented yet")


	class StreamContents:
		"""enumeration of possible PIP-Placements"""
		Live, Pause, NoStream = range(3)


	@controlServerEntrypoint
	def selectStreamContent(self, content):
		"""switch the livestream-content between selected mixer output, pause-image or nostream-imag"""
		assert(isinstance(content, StreamContents))
		raise NotImplementedError("pause/nostream switching is not implemented yet")
