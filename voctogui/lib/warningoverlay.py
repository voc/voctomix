import logging
from gi.repository import GLib, Gst, cairo

from lib.config import Config

class VideoWarningOverlay(object):
	""" Displays a Warning-Overlay above the Video-Feed of another VideoDisplay """

	def __init__(self):
		self.log = logging.getLogger('VideoWarningOverlay')

		self.text = None
		self.enabled = False
		self.blink_state = False

		GLib.timeout_add_seconds(1, self.on_blink_callback)

		caps_string = Config.get('mix', 'videocaps')
		self.log.debug('parsing video-caps: %s', caps_string)
		caps = Gst.Caps.from_string(caps_string)
		struct = caps.get_structure(0)
		_, self.width = struct.get_int('width')
		_, self.height = struct.get_int('height')

		self.log.debug('configuring size to %ux%u', self.width, self.height)


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

		w = self.width
		h = self.height / 20

		# during startup, cr is sometimes another kind of context,
		# which does not expose set_source_rgba and other methods.
		# this check avoids the exceptions that would be thrown then.
		if isinstance(cr, cairo.Context):
			return

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
