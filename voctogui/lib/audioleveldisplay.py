import logging
from gi.repository import Gst, Gtk

class AudioLevelDisplay(object):
	""" Displays a Level-Meter of another VideoDisplay into a GtkWidget """

	def __init__(self, drawing_area):
		self.log = logging.getLogger('AudioLevelDisplay[%s]' % drawing_area.get_name())

		self.drawing_area = drawing_area

		self.levelrms = [0, 0]  # Initialize to []
		self.drawing_area.connect('draw', self.on_draw)


	def on_draw(self, widget, cr):
		cr.set_source_rgb(1, 1, 1)
		cr.set_line_width(10)

		cr.move_to(15, 0)
		cr.line_to(15, self.levelrms[0]*-20)  # Work with 0+ Channels
		cr.stroke()

	def level_callback(self, peaks, rms):
		self.levelrms = rms
