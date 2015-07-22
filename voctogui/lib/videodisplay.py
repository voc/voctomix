import logging
from gi.repository import Gst, Gtk

class VideoDisplay:
	""" Displays a Voctomix-Video-Stream into a GtkWidget """

	def __init__(self, port, videowidget, audiolevelwidget=None, playaudio=False):
		self.log = logging.getLogger('VideoDisplay[%u]' % port)

		pipeline = """
			videotestsrc !
			timeoverlay !
			video/x-raw,width=1920,height=1080 !
			xvimagesink name=v
		""".format(
			port=port
		)

		if audiolevelwidget or playaudio:
			pipeline += """
				audiotestsrc wave=blue-noise !
				audio/x-raw !
				level name=lvl interval=50000000 !
			"""

			if playaudio:
				pipeline += """
					alsasink
				"""
			else:
				pipeline += """
					fakesink
				"""

		self.log.info('launching gstreamer-pipeline for widget %s "%s":\n%s', videowidget.get_name(), Gtk.Buildable.get_name(videowidget), pipeline)

		self.pipeline = Gst.parse_launch(pipeline)

		videowidget.realize()
		self.xid = videowidget.get_property('window').get_xid()

		bus = self.pipeline.get_bus()
		bus.add_signal_watch()
		bus.enable_sync_message_emission()

		bus.connect('message::error', self.on_error)
		bus.connect("sync-message::element", self.on_syncmsg)

		if audiolevelwidget:
			self.levelrms = [0, 0]
			self.audiolevelwidget = audiolevelwidget
			self.audiolevelwidget.connect('draw', self.on_level_draw)
			bus.connect("message::element", self.on_level)

	def run(self):
		self.pipeline.set_state(Gst.State.PLAYING)

	def set_overlay_callback(self, callback):
		if callback:
			if not self.draw_callback:
				self.draw_callback = self.pipeline.get_by_name('overlay').connect('draw', callback)
		else:
			print('disconnect')
			self.pipeline.get_by_name('overlay').disconnect(self.draw_callback)
			self.draw_callback = None

	def on_syncmsg(self, bus, msg):
		if msg.get_structure().get_name() == "prepare-window-handle":
				self.log.info('setting xvimagesink window-handle to %s', self.xid)
				msg.src.set_window_handle(self.xid)

	def on_error(self, bus, msg):
		self.log.error('on_error(): %s', msg.parse_error())

	def on_level_draw(self, widget, cr):
		cr.set_source_rgb(1, 1, 1)
		cr.set_line_width(10)

		cr.move_to(15, 0)
		cr.line_to(15, self.levelrms[0]*-20)
		cr.stroke()

	def on_level(self, bus, msg):
		if msg.src.name != 'lvl':
			return

		if msg.type != Gst.MessageType.ELEMENT:
			return

		self.levelpeaks = msg.get_structure().get_value('peak')
		self.levelrms = msg.get_structure().get_value('rms')
		self.audiolevelwidget.queue_draw()
