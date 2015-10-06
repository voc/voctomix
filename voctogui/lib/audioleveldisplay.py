import logging
from gi.repository import Gst, Gtk

class AudioLevelDisplay(object):
	""" Displays a Level-Meter of another VideoDisplay into a GtkWidget """

	def __init__(self, drawing_area):
		self.log = logging.getLogger('AudioLevelDisplay[%s]' % drawing_area.get_name())

		self.drawing_area = drawing_area

		self.levelrms = []
		self.drawing_area.connect('draw', self.on_draw)

	def on_draw(self, widget, cr):
		channels = len(self.levelrms)

		if channels == 0:
			return

		width = self.drawing_area.get_allocated_width()
		height = self.drawing_area.get_allocated_height()

		strip_width = int(width / 2)
		#self.log.debug('width: %u, strip_width: %u', width, strip_width)

		cr.set_line_width(strip_width)

		maxdb = -75

		for idx, level in enumerate(self.levelrms):
			level = level / maxdb

			x = idx * strip_width + strip_width/2
			#self.log.debug('x: %u', x)

			cr.move_to(x, height)
			cr.line_to(x, height * level)

			if idx % 2 == 0:
				cr.set_source_rgb(1, 0, 0)
			else:
				cr.set_source_rgb(0, 1, 0)

			cr.stroke()

		return True

	def level_callback(self, peaks, rms):
		self.levelrms = rms
		self.drawing_area.queue_draw()
