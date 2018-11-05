import math
import cairo

from lib.config import Config
from gi.repository import Gtk, GLib, Gst


class AudioLevelDisplay(Gtk.DrawingArea):
    """Displays a Level-Meter of another VideoDisplay into a GtkWidget"""
    __gtype_name__ = 'AudioLevelDisplay'

    def __init__(self):
        self.num_audiostreams_ = int(Config.get('mix', 'audiostreams'))
        meters = Config.get('mainvideo', 'vumeter')
        if (meters != 'all') and (int(meters) < self.num_audiostreams_):
            self.num_audiostreams_ = int(meters)

        self.channels = 2
        acaps = Gst.Caps.from_string(Config.get('mix', 'audiocaps'))
        self.channels = int(acaps.get_structure(0).get_int("channels")[1])

        self.levelrms = [0] * self.channels * self.num_audiostreams_
        self.levelpeak = [0] * self.channels * self.num_audiostreams_
        self.leveldecay = [0] * self.channels * self.num_audiostreams_

        self.height = -1

        self.set_size_request(20 * self.num_audiostreams_, -1)

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

        width = self.get_allocated_width()
        height = self.get_allocated_height()

        # space between the channels in px
        margin = 2

        # 1 channel -> 0 margins, 2 channels -> 1 margin, 3 channels…
        channel_width = int((width - (margin * (channels - 1))) / channels)

        # self.log.debug(
        #     'width: %upx filled with %u channels of each %upx '
        #     'and %ux margin of %upx',
        #     width, channels, channel_width, channels - 1, margin
        # )

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

        # draw all level bars for all channels
        for channel in range(0, channels):
            # start-coordinate for this channel
            x = (channel * channel_width) + (channel * margin)

            # draw background
            cr.rectangle(x, 0, channel_width, height - peak_px[channel])
            cr.set_source(self.bg_lg)
            cr.fill()

            # draw peak bar
            cr.rectangle(
                x, height - peak_px[channel], channel_width, peak_px[channel])
            cr.set_source(self.peak_lg)
            cr.fill()

            # draw rms bar below
            cr.rectangle(
                x, height - rms_px[channel], channel_width,
                rms_px[channel] - peak_px[channel])
            cr.set_source(self.rms_lg)
            cr.fill()

            # draw decay bar
            cr.rectangle(x, height - decay_px[channel], channel_width, 2)
            cr.set_source(self.decay_lg)
            cr.fill()

            # draw medium grey margin bar
            if margin > 0:
                cr.rectangle(x + channel_width, 0, margin, height)
                cr.set_source_rgb(0.5, 0.5, 0.5)
                cr.fill()

        # draw db text-markers
        for db in [-40, -20, -10, -5, -4, -3, -2, -1]:
            text = str(db)
            (xbearing, ybearing,
             textwidth, textheight,
             xadvance, yadvance) = cr.text_extents(text)

            y = self.normalize_db(db) * height
            if y > peak_px[channels - 1]:
                cr.set_source_rgb(1, 1, 1)
            else:
                cr.set_source_rgb(0, 0, 0)
            cr.move_to((width - textwidth) - 2, height - y - textheight)
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

    def level_callback(self, rms, peak, decay, stream):
        meter_offset = self.channels * stream
        for i in range(0, self.channels):
            self.levelrms[meter_offset + i] = rms[i]
            self.levelpeak[meter_offset + i] = peak[i]
            self.leveldecay[meter_offset + i] = decay[i]
        self.queue_draw()
