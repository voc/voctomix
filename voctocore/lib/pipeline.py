#!/usr/bin/python3
import os, errno, time, logging
from gi.repository import GLib, Gst

# import controlserver annotation
from lib.controlserver import controlServerEntrypoint

# import library components
from lib.config import Config
from lib.quadmix import QuadMix
from lib.videomix import VideoMix
# from lib.audiomix import AudioMix
from lib.distributor import TimesTwoDistributor
from lib.shmsrc import FailsafeShmSrc

class Pipeline(Gst.Pipeline):
	"""mixing, streaming and encoding pipeline constuction and control"""
	log = logging.getLogger('Pipeline')
	videonames = []
	audionames = []

	def __init__(self):
		super().__init__()

		self.log.debug('Creating Video-Mixer')
		# create audio and video mixer
		self.quadmixer = QuadMix()
		self.add(self.quadmixer)

		self.videomixer = VideoMix()
		self.add(self.videomixer)

		# self.audiomixer = AudioMix()
		# self.add(self.audiomixer)

		# read the path where the shm-control-sockets are located and ensure it exists
		socketpath = Config.get('sources', 'socketpath')
		self.log.info('Ensuring the configured socketpath exists: %s', socketpath)
		try:
			os.makedirs(socketpath)
		except OSError as exception:
			if exception.errno != errno.EEXIST:
				raise

		self.videonames = Config.getlist('sources', 'video')
		self.audionames = Config.getlist('sources', 'video')

		for name in self.videonames:
			socket = os.path.join(socketpath, 'v-'+name)

			self.log.info('Creating video-source "%s" at socket-path %s', name, socket)
			sourcebin = FailsafeShmSrc(socket)
			self.add(sourcebin)

			distributor = TimesTwoDistributor()
			self.add(distributor)
			sourcebin.link(distributor)

			mixerpad = self.quadmixer.request_mixer_pad()
			distributor.get_static_pad('src_a').link(mixerpad)

			mixerpad = self.videomixer.request_mixer_pad()
			distributor.get_static_pad('src_b').link(mixerpad)

		# for audiosource in Config.getlist('sources', 'audio'):
		# 	sourcebin = FailsafeShmSrc(os.path.join(socketpath, audiosource))

		# 	self.add(sourcebin)
		# 	sourcebin.link(self.audiomixer)

		# tell the quadmix that this were all sources and no more sources will come after this
		self.quadmixer.finalize()

		self.quadmixer.set_active(0)
		self.videomixer.set_active(0)

		self.quadmixsink = Gst.ElementFactory.make('autovideosink', 'quadmixsink')
		self.quadmixsink.set_property('sync', False)
		self.add(self.quadmixsink)
		self.quadmixer.link(self.quadmixsink)

		self.videosink = Gst.ElementFactory.make('autovideosink', 'videosink')
		self.videosink.set_property('sync', False)
		self.add(self.videosink)
		self.videomixer.link(self.videosink)

		# self.audiosink = Gst.ElementFactory.make('autoaudiosink', 'audiosink')
		# self.add(self.audiosink)
		# self.audiomixer.link(self.audiosink)

	def run(self):
		self.set_state(Gst.State.PAUSED)
		time.sleep(0.5)
		self.set_state(Gst.State.PLAYING)

	def quit(self):
		self.set_state(Gst.State.NULL)




	# 	# collection of video-sources to connect to the quadmix
	# 	quadmixSources = []

	# 	# create camera sources
	# 	for camberabin in self.createDummyCamSources():
	# 		# link camerasource to audiomixer
	# 		camberabin.get_by_name('audio_src').link(self.pipeline.get_by_name('liveaudio'))

	# 		# inject a ×2 distributor and link one end to the live-mixer
	# 		distributor = self.createDistributor(camberabin.get_by_name('video_src'), camberabin.get_name())
	# 		distributor.get_by_name('a').link(self.pipeline.get_by_name('livevideo'))

	# 		# collect the other end to add it later to the quadmix
	# 		quadmixSources.append(distributor.get_by_name('b'))

	# 	# TODO: generate pause & slides with another generator here which only
	# 	# yields if the respective files are present and which only have a video-pad

	# 	# add all video-sources to the quadmix-monitor-screen
	# 	self.addVideosToQuadmix(quadmixSources, self.pipeline.get_by_name('quadmix'))

	# 	# initialize to known defaults
	# 	# TODO: make configurable
	# 	self.switchVideo(0)
	# 	self.switchAudio(0)

	# 	Gst.debug_bin_to_dot_file(self.pipeline, Gst.DebugGraphDetails.ALL, 'test')
	# 	self.pipeline.set_state(Gst.State.PLAYING)






	# def createMixer(self):
	# 	"""create audio and video mixer"""
	# 	# create mixer-pipeline from string
	# 	mixerbin = Gst.parse_bin_from_description("""
	# 		videomixer name=livevideo ! autovideosink
	# 		input-selector name=liveaudio ! autoaudiosink

	# 		videotestsrc pattern="solid-color" foreground-color=0x808080 ! capsfilter name=filter ! videomixer name=quadmix ! autovideosink
	# 	""", False)

	# 	# define caps for the videotestsrc which generates the background-color for the quadmix
	# 	bgcaps = Gst.Caps.new_empty_simple('video/x-raw')
	# 	bgcaps.set_value('width', round(self.monitorSize[0]))
	# 	bgcaps.set_value('height', round(self.monitorSize[1]))
	# 	mixerbin.get_by_name('filter').set_property('caps', bgcaps)

	# 	# name the bin, add and return it
	# 	mixerbin.set_name('mixerbin')
	# 	self.pipeline.add(mixerbin)
	# 	return mixerbin

	# def addVideosToQuadmix(self, videosources, quadmix):
	# 	"""add all avaiable videosources to the quadmix"""
	# 	count = len(videosources)

	# 	# coordinate of the cell where we place the next video
	# 	place = [0, 0]
		
	# 	# number of cells in the quadmix-monitor
	# 	grid = [0, 0]
	# 	grid[0] = math.ceil(math.sqrt(count))
	# 	grid[1] = math.ceil(count / grid[0])

	# 	# size of each cell in the quadmix-monitor
	# 	cellSize = (
	# 		self.monitorSize[0] / grid[0],
	# 		self.monitorSize[1] / grid[1]
	# 	)

	# 	print("showing {} videosources in a {}×{} grid in a {}×{} px window, which gives cells of {}×{} px per videosource".format(
	# 		count, grid[0], grid[1], self.monitorSize[0], self.monitorSize[1], cellSize[0], cellSize[1]))

	# 	# iterate over all video-sources
	# 	for idx, videosource in enumerate(videosources):
	# 		# generate a pipeline for this videosource which
	# 		# - scales the video to the request
	# 		# - remove n px of the video (n = 5 if the video is highlighted else 0)
	# 		# - add a colored border of n px of the video (n = 5 if the video is highlighted else 0)
	# 		# - overlay the index of the video as text in the top left corner
	# 		# - known & named output
	# 		previewbin = Gst.parse_bin_from_description("""
	# 			videoscale name=in !
	# 			capsfilter name=caps !
	# 			videobox name=crop top=0 left=0 bottom=0 right=0 !
	# 			videobox fill=red top=-0 left=-0 bottom=-0 right=-0 name=add !
	# 			textoverlay color=0xFFFFFFFF halignment=left valignment=top xpad=10 ypad=5 font-desc="sans 35" name=text !
	# 			identity name=out
	# 		""", False)

	# 		# name the bin and add it
	# 		previewbin.set_name('previewbin-{}'.format(idx))
	# 		self.pipeline.add(previewbin)
	# 		self.previewbins.append(previewbin)

	# 		# set the overlay-text
	# 		previewbin.get_by_name('text').set_property('text', str(idx))

	# 		# query the video-source caps and extract its size
	# 		caps = videosource.get_static_pad('src').query_caps(None)
	# 		capsstruct = caps.get_structure(0)
	# 		srcSize = (
	# 			capsstruct.get_int('width')[1],
	# 			capsstruct.get_int('height')[1],
	# 		)

	# 		# calculate the ideal scale factor and scale the sizes
	# 		f = max(srcSize[0] / cellSize[0], srcSize[1] / cellSize[1])
	# 		scaleSize = (
	# 			srcSize[0] / f,
	# 			srcSize[1] / f,
	# 		)

	# 		# calculate the top/left coordinate
	# 		coord = (
	# 			place[0] * cellSize[0] + (cellSize[0] - scaleSize[0]) / 2,
	# 			place[1] * cellSize[1] + (cellSize[1] - scaleSize[1]) / 2,
	# 		)

	# 		print("placing videosource {} of size {}×{} scaled by {} to {}×{} in a cell {}×{} px cell ({}/{}) at position ({}/{})".format(
	# 			idx, srcSize[0], srcSize[1], f, scaleSize[0], scaleSize[1], cellSize[0], cellSize[1], place[0], place[1], coord[0], coord[1]))

	# 		# link the videosource to the input of the preview-bin
	# 		videosource.link(previewbin.get_by_name('in'))

	# 		# create and set the caps for the preview-scaler
	# 		scalecaps = Gst.Caps.new_empty_simple('video/x-raw')
	# 		scalecaps.set_value('width', round(scaleSize[0]))
	# 		scalecaps.set_value('height', round(scaleSize[1]))
	# 		previewbin.get_by_name('caps').set_property('caps', scalecaps)

	# 		# request a pad from the quadmixer and configure x/y position
	# 		sinkpad = quadmix.get_request_pad('sink_%u')
	# 		sinkpad.set_property('xpos', round(coord[0]))
	# 		sinkpad.set_property('ypos', round(coord[1]))

	# 		# link the output of the preview-bin to the mixer
	# 		previewbin.get_by_name('out').link(quadmix)

	# 		# increment grid position
	# 		place[0] += 1
	# 		if place[0] >= grid[0]:
	# 			place[1] += 1
	# 			place[0] = 0

	# def createDistributor(self, videosource, name):
	# 	"""create a simple ×2 distributor"""
	# 	distributor = Gst.parse_bin_from_description("""
	# 		tee name=t
	# 		t. ! queue name=a
	# 		t. ! queue name=b
	# 	""", False)

	# 	# set a name and add to pipeline
	# 	distributor.set_name('distributor({0})'.format(name))
	# 	self.pipeline.add(distributor)

	# 	# link input to the tee
	# 	videosource.link(distributor.get_by_name('t'))
	# 	return distributor

	# def createDummyCamSources(self):
	# 	"""create test-video-sources from files or urls"""

	# 	# TODO make configurable
	# 	uris = ('file:///home/peter/122.mp4', 'file:///home/peter/10025.mp4',)
	# 	for idx, uri in enumerate(uris):
	# 		# create a bin for a simulated camera input
	# 		# force the input resolution to 1024x576 because that way the following elements
	# 		# in the pipeline cam know the size even if the file is not yet loaded. the quadmixer
	# 		# is not resize-capable
	# 		camberabin = Gst.parse_bin_from_description("""
	# 			uridecodebin name=input
	# 			input. ! videoconvert ! videoscale ! videorate ! video/x-raw,width=1024,height=576,framerate=25/1 ! identity name=video_src
	# 			input. ! audioconvert name=audio_src
	# 		""", False)

	# 		# set name and uri
	# 		camberabin.set_name('dummy-camberabin({0})'.format(uri))
	# 		camberabin.get_by_name('input').set_property('uri', uri)

	# 		# add to pipeline and pass the bin upstream
	# 		self.pipeline.add(camberabin)
	# 		yield camberabin


	# def createCamSources(self):
	# 	"""create real-video-sources from the bmd-drivers"""

	# 	# TODO make number of installed cams configurable
	# 	for cam in range(2):
	# 		# create a bin for camera input
	# 		camberabin = Gst.parse_bin_from_description("""
	# 			decklinksrc name=input input=sdi input-mode=1080p25
	# 			input. ! videoconvert ! videoscale ! videorate ! video/x-raw,width=1920,height=1080,framerate=25/1 ! identity name=video_src
	# 			input. ! audioconvert name=audio_src
	# 		""", False)

	# 		# set name and subdevice
	# 		camberabin.set_name('camberabin({0})'.format(cam))
	# 		camberabin.get_by_name('input').set_property('subdevice', cam)

	# 		# add to pipeline and pass the bin upstream
	# 		self.pipeline.add(camberabin)
	# 		yield camberabin




	### below are access-methods for the ControlServer
	@controlServerEntrypoint
	def status(self):
		"""System Status Query"""
		raise NotImplementedError("status command is not implemented yet")

	@controlServerEntrypoint
	def numAudioSources(self):
		"""return number of available audio sources"""
		raise NotImplementedError("audio is not implemented yet")


	@controlServerEntrypoint
	def switchAudio(self, audiosource):
		"""switch audio to the selected audio"""
		raise NotImplementedError("audio is not implemented yet")


	@controlServerEntrypoint
	def numVideoSources(self):
		"""return number of available video sources"""
		livevideo = self.pipeline.get_by_name('livevideo')
		return str(len(self.videonames))


	@controlServerEntrypoint
	def switchVideo(self, videosource):
		"""switch audio to the selected video"""
		if videosource.isnumeric():
			idx = int(videosource)
			self.log.info("interpreted input as videosource-index %u", idx)
			if idx >= len(self.videonames):
				idx = None
		else:
			try:
				idx = self.videonames.index(videosource)
				self.log.info("interpreted input as videosource-name, lookup to %u", idx)
			except IndexError:
				idx = None

		if idx == None:
			return 'unknown video-source: %s' % (videosource)

		self.log.info("switching quadmix to video-source %u", idx)
		self.quadmixer.set_active(idx)
		self.videomixer.set_active(idx)


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
