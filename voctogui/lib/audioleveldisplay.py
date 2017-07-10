import logging
import math


class AudioLevelDisplay(object):
    """Displays a Level-Meter of another VideoDisplay into a GtkWidget"""

    def __init__(self, drawing_area):
        self.log = logging.getLogger(
            'AudioLevelDisplay[{}]'.format(drawing_area.get_name())
        )

        self.drawing_area = drawing_area

        self.levelrms = []
        self.levelpeak = []
        self.leveldecay = []

        # register on_draw handler
        self.drawing_area.connect('draw', self.on_draw)

    def on_draw(self, widget, cr):
        # number of audio-channels
        channels = len(self.levelrms)

        if channels == 0:
            return False

        width = self.drawing_area.get_allocated_width()
        height = self.drawing_area.get_allocated_height()

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

        # set the line-width >1, to get a nice overlap
        cr.set_line_width(2)

        # iterate over all pixels
        for y in range(0, height):

            # calculate our place in the color-gradient, clamp to 0…1
            # 0 -> green, 0.5 -> yellow, 1 -> red
            color = self.clamp(((y / height) - 0.6) / 0.42)

            for channel in range(0, channels):
                # start-coordinate for this channel
                x = (channel * channel_width) + (channel * margin)

                # calculate the brightness based on whether this line is in the
                # active region

                # default to 0.25, dark
                bright = 0.25
                if int(y - decay_px[channel]) in range(0, 2):
                    # decay marker, 2px wide, extra bright
                    bright = 1.5
                elif y < rms_px[channel]:
                    # rms bar, full bright
                    bright = 1
                elif y < peak_px[channel]:
                    # peak bar, a little darker
                    bright = 0.75

                # set the color with a little reduced green
                cr.set_source_rgb(
                    color * bright,
                    (1 - color) * bright * 0.75,
                    0
                )

                # draw the marker
                cr.move_to(x, height - y)
                cr.line_to(x + channel_width, height - y)
                cr.stroke()

                # draw a black line for the margin
                cr.set_source_rgb(0, 0, 0)
                cr.move_to(x + channel_width, height - y)
                cr.line_to(x + channel_width + margin, height - y)
                cr.stroke()

        # draw db text-markers
        cr.set_source_rgb(1, 1, 1)
        for db in [-40, -20, -10, -5, -4, -3, -2, -1]:
            text = str(db)
            (xbearing, ybearing,
             textwidth, textheight,
             xadvance, yadvance) = cr.text_extents(text)

            y = self.normalize_db(db) * height
            cr.move_to((width - textwidth) / 2, height - y - textheight)
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
        self.levelrms = rms
        self.levelpeak = peak
        self.leveldecay = decay
        self.drawing_area.queue_draw()
