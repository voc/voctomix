import logging
from gi.repository import GLib


class VideoWarningOverlay(object):
    """Displays a Warning-Overlay above the Video-Feed
       of another VideoDisplay"""

    def __init__(self, drawing_area):
        self.log = logging.getLogger('VideoWarningOverlay')

        self.drawing_area = drawing_area
        self.drawing_area.connect("draw", self.draw_callback)

        self.text = None
        self.blink_state = False

        GLib.timeout_add_seconds(1, self.on_blink_callback)

    def on_blink_callback(self):
        self.blink_state = not self.blink_state
        self.drawing_area.queue_draw()
        return True

    def enable(self, text=None):
        self.text = text
        self.drawing_area.show()
        self.drawing_area.queue_draw()

    def set_text(self, text=None):
        self.text = text
        self.drawing_area.queue_draw()

    def disable(self):
        self.drawing_area.hide()
        self.drawing_area.queue_draw()

    def draw_callback(self, drawing_area, cr):
        w = drawing_area.get_allocated_width()
        h = drawing_area.get_allocated_height()

        if self.blink_state:
            cr.set_source_rgba(1.0, 0.0, 0.0, 0.8)
        else:
            cr.set_source_rgba(1.0, 0.5, 0.0, 0.8)

        cr.rectangle(0, 0, w, h)
        cr.fill()

        text = "Stream is Blanked"
        if self.text:
            text += ": " + self.text

        cr.set_font_size(h * 0.75)
        (xbearing, ybearing,
         txtwidth, txtheight,
         xadvance, yadvance) = cr.text_extents(text)

        cr.move_to(w / 2 - txtwidth / 2, h * 0.75)
        cr.set_source_rgba(1.0, 1.0, 1.0, 1.0)
        cr.show_text(text)
