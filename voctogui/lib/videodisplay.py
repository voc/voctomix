import logging
from gi.repository import Gst, Gtk

class VideoDisplay:
	""" Displays a Voctomix-Video-Stream into a GtkWidget """

	def __init__(self, port, widget):
		self.log = logging.getLogger('VideoDisplay[%u]' % port)

		pipeline = """
			videotestsrc !
			timeoverlay !
			video/x-raw,width=1920,height=1080 !
			xvimagesink
		""".format(
			port=port
		)
		self.log.info('launching gstreamer-pipeline for widget %s "%s":\n%s', widget.get_name(), Gtk.Buildable.get_name(widget), pipeline)

		self.pipeline = Gst.parse_launch(pipeline)

		widget.realize()
		self.xid = widget.get_property('window').get_xid()

		bus = self.pipeline.get_bus()
		bus.add_signal_watch()
		bus.enable_sync_message_emission()

		bus.connect('message::error', self.on_error)
		bus.connect("sync-message::element", self.on_syncmsg)

	def run(self):
		self.pipeline.set_state(Gst.State.PLAYING)

	def on_syncmsg(self, bus, msg):
		if msg.get_structure().get_name() == "prepare-window-handle":
				self.log.info('setting xvimagesink window-handle to %s', self.xid)
				msg.src.set_window_handle(self.xid)

	def on_error(self, bus, msg):
			self.log.error('on_error():', msg.parse_error())
