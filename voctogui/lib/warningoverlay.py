import logging

from gi.repository import GLib

import lib.connection as Connection


class VideoWarningOverlay(object):
    """Displays a Warning-Overlay above the Video-Feed
       of another VideoDisplay"""

    def __init__(self, drawing_area):
        self.log = logging.getLogger('VideoWarningOverlay')

        self.drawing_area = drawing_area
        self.drawing_area.connect("draw", self._draw_callback)

        self.streamblank_text = None
        self.notification_text = None
        self.blink_state = False

        Connection.on('show_notification', self._on_show_notification)
        Connection.on('hide_notification', self._on_hide_notification)

        GLib.timeout_add_seconds(1, self._on_blink_callback)

    def enable_streamblank_warning(self, text=None):
        display_text = "Stream is Blanked"
        if text:
            display_text = display_text + ": " + text

        self.streamblank_text = display_text
        self._update_overlay_state()

    def disable_notification(self):
        self.notification_text = None
        self._update_overlay_state()

    def enable_notification(self, text):
        self.notification_text = text
        self._update_overlay_state()

    def disable_streamblank_warning(self):
        self.streamblank_text = None
        self._update_overlay_state()

    def _update_overlay_state(self):
        if self.streamblank_text or self.notification_text:
            self.drawing_area.show()
            self.drawing_area.queue_draw()
        else:
            self.drawing_area.hide()

    def _on_blink_callback(self):
        self.blink_state = not self.blink_state
        self.drawing_area.queue_draw()
        return True

    def _on_show_notification(self, *args):
        self.enable_notification(' '.join(args))

    def _on_hide_notification(self):
        self.disable_notification()

    def _draw_callback(self, drawing_area, cr):
        w = drawing_area.get_allocated_width()
        h = drawing_area.get_allocated_height()

        if self.notification_text:
            text = self.notification_text
            color = (0.0, 0.0, 1.0, 0.8) if self.blink_state else (0.3, 0.3, 0.8, 0.8)

        elif self.streamblank_text:
            text = self.streamblank_text
            color = (1.0, 0.0, 0.0, 0.8) if self.blink_state else (1.0, 0.5, 0.0, 0.8)

        else:
            return

        cr.set_source_rgba(*color)

        cr.rectangle(0, 0, w, h)
        cr.fill()

        cr.set_font_size(h * 0.75)
        (xbearing, ybearing,
         txtwidth, txtheight,
         xadvance, yadvance) = cr.text_extents(text)

        cr.move_to(w / 2 - txtwidth / 2, h * 0.75)
        cr.set_source_rgba(1.0, 1.0, 1.0, 1.0)
        cr.show_text(text)
