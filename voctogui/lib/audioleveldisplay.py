import logging, math
from gi.repository import Gst, Gtk

class AudioLevelDisplay(object):
	""" Displays a Level-Meter of another VideoDisplay into a GtkWidget """

	def __init__(self, drawing_area):
		self.log = logging.getLogger('AudioLevelDisplay[%s]' % drawing_area.get_name())

		self.drawing_area = drawing_area

		self.levelrms = []
		self.levelpeak = []
		self.leveldecay = []
		self.drawing_area.connect('draw', self.on_draw)

	def on_draw(self, widget, cr):
		channels = len(self.levelrms)

		if channels == 0:
			return

		width = self.drawing_area.get_allocated_width()
		height = self.drawing_area.get_allocated_height()
		margin = 2 # px

		channel_width = int((width - (margin * (channels - 1))) / channels)
		# self.log.debug(
		# 	'width: %upx filled with %u channels of each %upx '
		# 	'and %ux margin of %upx',
		# 	width, channels, channel_width, channels-1, margin)

		rms_px   = [ self.normalize_db(db) * height for db in self.levelrms ]
		peak_px  = [ self.normalize_db(db) * height for db in self.levelpeak ]
		decay_px = [ self.normalize_db(db) * height for db in self.leveldecay ]

		cr.set_line_width(channel_width)
		for y in range(0, height):
			pct = y / height

			for channel in range(0, channels):
				x = (channel * channel_width) + (channel * margin)

				bright = 0.25
				if y < rms_px[channel]:
					bright = 1
				# elif abs(y - peak_px[channel]) < 3:
				# 	bright = 1.5
				elif y < decay_px[channel]:
					bright = 0.75

				cr.set_source_rgb(pct * bright, (1-pct) * bright, 0 * bright)

				cr.move_to(x, height-y)
				cr.line_to(x + channel_width, height-y)
				cr.stroke()

		return True

	def normalize_db(self, db):
		# -60db -> 1.00 (very quiet)
		# -30db -> 0.75
		# -15db -> 0.50
		#  -5db -> 0.25
		#  -0db -> 0.00 (very loud)
		logscale = math.log10(-0.15* (db) +1)
		normalized = 1 - self.clamp(logscale, 0, 1)
		return normalized

	def clamp(self, value, min_value, max_value):
		return max(min(value, max_value), min_value)

	def level_callback(self, rms, peak, decay):
		self.levelrms = rms
		self.levelpeak = peak
		self.leveldecay = decay
		self.drawing_area.queue_draw()
