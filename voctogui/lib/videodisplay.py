import logging
from gi.repository import Gst

class VideoDisplay:
	""" Displays a Voctomix-Video-Stream into a GtkWidget """

	def __init__(self, drawing_area, port, play_audio=False, draw_callback=None, level_callback=None):
		self.log = logging.getLogger('VideoDisplay[%s]' % drawing_area.get_name())

		self.drawing_area = drawing_area
		self.draw_callback = draw_callback
		self.level_callback = level_callback

		# Setup Server-Connection, Demuxing and Decoding
		pipeline = """
			videotestsrc !
			timeoverlay !
			video/x-raw,width=1920,height=1080,framerate=25/1 !
		""".format(
			port=port
		)

		# If an overlay is required, add an cairooverlay-Element into the Video-Path
		if self.draw_callback:
			pipeline += """
				videoconvert !
				cairooverlay name=overlay !
				videoconvert !
			"""

		# Video Display
		pipeline += """
			xvimagesink name=v
		"""


		# If an Audio-Path is required, add an Audio-Path through a level-Element
		if self.level_callback or play_audio:
			pipeline += """
				audiotestsrc wave=blue-noise !
				audio/x-raw !
				level name=lvl interval=50000000 !
			"""

			# If Playback is requested, push fo alsa
			if play_audio:
				pipeline += """
					alsasink
				"""

			# Otherwise just trash the Audio
			else:
				pipeline += """
					fakesink
				"""

		self.log.debug('Creating Display-Pipeline:\n%s', pipeline)
		self.pipeline = Gst.parse_launch(pipeline)

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

		if self.draw_callback:
			self.pipeline.get_by_name('overlay').connect('draw', self.on_draw)

		self.log.debug('Launching Display-Pipeline')
		self.pipeline.set_state(Gst.State.PLAYING)


	def on_syncmsg(self, bus, msg):
		if msg.get_structure().get_name() == "prepare-window-handle":
				self.log.info('Setting xvimagesink window-handle to %s', self.xid)
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

		peaks = msg.get_structure().get_value('peak')
		rms = msg.get_structure().get_value('rms')
		self.level_callback(peaks, rms)

	def on_draw(self, cairooverlay, cr, timestamp, duration):
		self.draw_callback(cr, timestamp, duration)
