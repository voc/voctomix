import math
import cairo

from gi.repository import Gtk, GLib


class AudioLevelDisplay(Gtk.DrawingArea):
    """Displays a Level-Meter of another VideoDisplay into a GtkWidget"""

    __gtype_name__ = 'AudioLevelDisplay'

    MARGIN = 4
    CHANNEL_WIDTH = 8
    LABEL_WIDTH = 20

    def __init__(self):
        self.levelrms = []
        self.levelpeak = []
        self.leveldecay = []

        self.height = -1

        # register on_draw handler
        self.connect('draw', self.draw_callback)

    # generate gradient from green to yellow to red in logarithmic scale
    def gradient(self, brightness, darkness, height):
        # prepare gradient
        lg = cairo.LinearGradient(0, 0, 0, height)
        # set gradient stops
        lg.add_color_stop_rgb(0.0, brightness, darkness, darkness)
        lg.add_color_stop_rgb(0.22, brightness, brightness, darkness)
        lg.add_color_stop_rgb(0.25, brightness, brightness, darkness)
        lg.add_color_stop_rgb(0.35, darkness, brightness, darkness)
        lg.add_color_stop_rgb(1.0, darkness, brightness, darkness)
        # return result
        return lg

    def draw_callback(self, widget, cr):
        # number of audio-channels
        channels = len(self.levelrms)

        if channels == 0:
            return False

        yoff = 3
        width = self.get_allocated_width()
        height = self.get_allocated_height() - yoff

        # normalize db-value to 0…1 and multiply with the height
        rms_px = [self.normalize_db(db) * height for db in self.levelrms]
        peak_px = [self.normalize_db(db) * height for db in self.levelpeak]
        decay_px = [self.normalize_db(db) * height for db in self.leveldecay]

        if self.height != height:
            self.height = height
            # setup gradients for all level bars
            self.bg_lg = self.gradient(0.25, 0.0, height)
            self.rms_lg = self.gradient(1.0, 0.0, height)
            self.peak_lg = self.gradient(0.75, 0.0, height)
            self.decay_lg = self.gradient(1.0, 0.5, height)

        first_col = True
        # draw all level bars for all channels
        for channel in range(0, channels):
            # start-coordinate for this channel
            x = (
                (channel * self.CHANNEL_WIDTH)
                + (channel * self.MARGIN)
                + self.LABEL_WIDTH
            )

            # draw background
            cr.rectangle(x, yoff, self.CHANNEL_WIDTH, height - peak_px[channel])
            cr.set_source(self.bg_lg)
            cr.fill()

            # draw peak bar
            cr.rectangle(
                x,
                yoff + height - peak_px[channel],
                self.CHANNEL_WIDTH,
                peak_px[channel],
            )
            cr.set_source(self.peak_lg)
            cr.fill()

            # draw rms bar below
            cr.rectangle(
                x,
                yoff + height - rms_px[channel],
                self.CHANNEL_WIDTH,
                rms_px[channel] - peak_px[channel],
            )
            cr.set_source(self.rms_lg)
            cr.fill()

            # draw decay bar
            cr.rectangle(x, yoff + height - decay_px[channel], self.CHANNEL_WIDTH, 2)
            cr.set_source(self.decay_lg)
            cr.fill()

            first_col = False

            # draw db text-markers
            for db in [-40, -20, -10, -5, -4, -3, -2, -1]:
                text = str(db)
                (xbearing, ybearing, textwidth, textheight, xadvance, yadvance) = (
                    cr.text_extents(text)
                )

                y = self.normalize_db(db) * height
                cr.set_source_rgb(0.5, 0.5, 0.5)
                cr.move_to(
                    self.LABEL_WIDTH - textwidth - 4, yoff + height - y - textheight
                )
                cr.show_text(text)

        return True

    def normalize_db(self, db):
        # -60db -> 1.00 (very quiet)
        # -30db -> 0.75
        # -15db -> 0.50
        #  -5db -> 0.25
        #  -0db -> 0.00 (very loud)
        logscale = 1 - math.log10(-0.15 * db + 1)
        return self.clamp(logscale)

    def clamp(self, value, min_value=0, max_value=1):
        return max(min(value, max_value), min_value)

    def level_callback(self, rms, peak, decay):
        if self.levelrms != rms or self.levelpeak != peak or self.leveldecay != decay:
            self.levelrms = rms
            self.levelpeak = peak
            self.leveldecay = decay

            self.set_size_request(
                len(self.levelrms) * (self.CHANNEL_WIDTH + self.MARGIN)
                + self.LABEL_WIDTH,
                100,
            )
            self.queue_draw()
