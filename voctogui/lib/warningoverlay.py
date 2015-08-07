import logging
from gi.repository import GLib

class VideoWarningOverlay(object):
	""" Displays a Warning-Overlay above the Video-Feed of another VideoDisplay """

	def __init__(self):
		self.log = logging.getLogger('VideoWarningOverlay')

		self.text = None
		self.enabled = False
		self.blink_state = False

		GLib.timeout_add_seconds(1, self.on_blink_callback)


	def on_blink_callback(self):
		self.blink_state = not self.blink_state
		return True

	def enable(self, text=None):
		self.text = text
		self.enabled = True

	def set_text(self, text=None):
		self.text = text

	def disable(self):
		self.enabled = False

	def draw_callback(self, cr, timestamp, duration):
		if not self.enabled:
			return

		w = 1920
		h = 1080/20

		if self.blink_state:
			cr.set_source_rgba(1.0, 0.0, 0.0, 0.8)
		else:
			cr.set_source_rgba(1.0, 0.5, 0.0, 0.8)

		cr.rectangle(0, 0, w, h)
		cr.fill()

		text = "Stream is Blanked"
		if self.text:
			text += ": "+self.text

		cr.set_font_size(h*0.75)
		xbearing, ybearing, txtwidth, txtheight, xadvance, yadvance = cr.text_extents(text)

		cr.move_to(w/2 - txtwidth/2, h*0.75)
		cr.set_source_rgba(1.0, 1.0, 1.0, 1.0)
		cr.show_text(text)
