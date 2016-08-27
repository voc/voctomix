import logging
from gi.repository import Gst

from lib.config import Config
from lib.clock import Clock

class VideoDisplay(object):
	""" Displays a Voctomix-Video-Stream into a GtkWidget """

	def __init__(self, drawing_area, port, width=None, height=None, play_audio=False, level_callback=None):
		self.log = logging.getLogger('VideoDisplay[%u]' % port)

		self.drawing_area = drawing_area
		self.level_callback = level_callback

		caps = Config.get('mix', 'videocaps')
		use_previews = Config.getboolean('previews', 'enabled') and Config.getboolean('previews', 'use')

		# Preview-Ports are Raw-Ports + 1000
		if use_previews:
			self.log.info('using jpeg-previews instead of raw-video for gui')
			port += 1000
		else:
			self.log.info('using raw-video instead of jpeg-previews for gui')

		# Setup Server-Connection, Demuxing and Decoding
		pipeline = """
			tcpclientsrc host={host} port={port} blocksize=1048576 !
			queue !
			matroskademux name=demux
		"""

		if use_previews:
			pipeline += """
				demux. !
				image/jpeg !
				jpegdec !
				{previewcaps} !
				queue !
			"""

		else:
			pipeline += """
				demux. !
				{vcaps} !
				queue !
			"""

		# Video Display
		videosystem = Config.get('videodisplay', 'system')
		self.log.debug('Configuring for Video-System %s', videosystem)
		if videosystem == 'gl':
			pipeline += """
				glupload !
				glcolorconvert !
				glimagesinkelement
			"""

		elif videosystem == 'xv':
			pipeline += """
				xvimagesink
			"""

		elif videosystem == 'x':
			prescale_caps = 'video/x-raw'
			if width and height:
				prescale_caps += ',width=%u,height=%u' % (width, height)

			pipeline += """
				videoconvert !
				videoscale !
				{prescale_caps} !
				ximagesink
			""".format(
				prescale_caps=prescale_caps
			)

		else:
			raise Exception('Invalid Videodisplay-System configured: %s' % videosystem)



		# If an Audio-Path is required, add an Audio-Path through a level-Element
		if self.level_callback or play_audio:
			pipeline += """
				demux. !
				{acaps} !
				queue !
				level name=lvl interval=50000000 !
			"""

			# If Playback is requested, push fo pulseaudio
			if play_audio:
				pipeline += """
					pulsesink
				"""

			# Otherwise just trash the Audio
			else:
				pipeline += """
					fakesink
				"""

		pipeline = pipeline.format(
			acaps=Config.get('mix', 'audiocaps'),
			vcaps=Config.get('mix', 'videocaps'),
			previewcaps=Config.get('previews', 'videocaps'),
			host=Config.get('server', 'host'),
			port=port,
		)

		self.log.debug('Creating Display-Pipeline:\n%s', pipeline)
		self.pipeline = Gst.parse_launch(pipeline)
		self.pipeline.use_clock(Clock)

		self.drawing_area.realize()
		self.xid = self.drawing_area.get_property('window').get_xid()
		self.log.debug('Realized Drawing-Area with xid %u', self.xid)

		bus = self.pipeline.get_bus()
		bus.add_signal_watch()
		bus.enable_sync_message_emission()

		bus.connect('message::error', self.on_error)
		bus.connect("sync-message::element", self.on_syncmsg)

		if self.level_callback:
			bus.connect("message::element", self.on_level)

		self.log.debug('Launching Display-Pipeline')
		self.pipeline.set_state(Gst.State.PLAYING)


	def on_syncmsg(self, bus, msg):
		if msg.get_structure().get_name() == "prepare-window-handle":
				self.log.info('Setting imagesink window-handle to %s', self.xid)
				msg.src.set_window_handle(self.xid)

	def on_error(self, bus, message):
		self.log.debug('Received Error-Signal on Display-Pipeline')
		(error, debug) = message.parse_error()
		self.log.debug('Error-Details: #%u: %s', error.code, debug)


	def on_level(self, bus, msg):
		if msg.src.name != 'lvl':
			return

		if msg.type != Gst.MessageType.ELEMENT:
			return

		rms = msg.get_structure().get_value('rms')
		peak = msg.get_structure().get_value('peak')
		decay = msg.get_structure().get_value('decay')
		self.level_callback(rms, peak, decay)
