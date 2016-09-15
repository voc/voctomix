import logging
from gi.repository import Gst, Gtk

from lib.config import Config
from lib.videodisplay import VideoDisplay
import lib.connection as Connection


class VideoPreviewsController(object):
    """Displays Video-Previews and selection Buttons for them"""

    def __init__(self, drawing_area, win, uibuilder):
        self.log = logging.getLogger('VideoPreviewsController')

        self.drawing_area = drawing_area
        self.win = win

        self.sources = Config.getlist('mix', 'sources')
        self.preview_players = {}
        self.previews = {}
        self.a_btns = {}
        self.b_btns = {}

        self.current_source = {'a': None, 'b': None}

        try:
            width = Config.getint('previews', 'width')
            self.log.debug('Preview-Width configured to %u', width)
        except:
            width = 320
            self.log.debug('Preview-Width selected as %u', width)

        try:
            height = Config.getint('previews', 'height')
            self.log.debug('Preview-Height configured to %u', height)
        except:
            height = width * 9 / 16
            self.log.debug('Preview-Height calculated to %u', height)

        # Accelerators
        accelerators = Gtk.AccelGroup()
        win.add_accel_group(accelerators)

        group_a = None
        group_b = None

        for idx, source in enumerate(self.sources):
            self.log.info('Initializing Video Preview %s', source)

            preview = uibuilder.get_check_widget('widget_preview', clone=True)
            video = uibuilder.find_widget_recursive(preview, 'video')

            video.set_size_request(width, height)
            drawing_area.pack_start(preview, fill=False,
                                    expand=False, padding=0)

            player = VideoDisplay(video, port=13000 + idx,
                                  width=width, height=height)

            uibuilder.find_widget_recursive(preview, 'label').set_label(source)
            btn_a = uibuilder.find_widget_recursive(preview, 'btn_a')
            btn_b = uibuilder.find_widget_recursive(preview, 'btn_b')

            btn_a.set_name("%c %u" % ('a', idx))
            btn_b.set_name("%c %u" % ('b', idx))

            if not group_a:
                group_a = btn_a
            else:
                btn_a.join_group(group_a)

            if not group_b:
                group_b = btn_b
            else:
                btn_b.join_group(group_b)

            btn_a.connect('toggled', self.btn_toggled)
            btn_b.connect('toggled', self.btn_toggled)

            key, mod = Gtk.accelerator_parse('%u' % (idx + 1))
            btn_a.add_accelerator('activate', accelerators,
                                  key, mod, Gtk.AccelFlags.VISIBLE)

            key, mod = Gtk.accelerator_parse('<Ctrl>%u' % (idx + 1))
            btn_b.add_accelerator('activate', accelerators,
                                  key, mod, Gtk.AccelFlags.VISIBLE)

            btn_fullscreen = uibuilder.find_widget_recursive(preview,
                                                             'btn_fullscreen')
            btn_fullscreen.set_name("%c %u" % ('f', idx))

            btn_fullscreen.connect('clicked', self.btn_fullscreen_clicked)

            key, mod = Gtk.accelerator_parse('<Alt>%u' % (idx + 1))
            btn_fullscreen.add_accelerator('activate', accelerators,
                                           key, mod, Gtk.AccelFlags.VISIBLE)

            self.preview_players[source] = player
            self.previews[source] = preview
            self.a_btns[source] = btn_a
            self.b_btns[source] = btn_b

        # connect event-handler and request initial state
        Connection.on('video_status', self.on_video_status)
        Connection.send('get_video')

    def btn_toggled(self, btn):
        if not btn.get_active():
            return

        btn_name = btn.get_name()
        self.log.debug('btn_toggled: %s', btn_name)

        channel, idx = btn_name.split(' ')[:2]
        source_name = self.sources[int(idx)]

        if self.current_source[channel] == source_name:
            self.log.info('video-channel %s already on %s',
                          channel, source_name)
            return

        self.log.info('video-channel %s changed to %s', channel, source_name)
        Connection.send('set_video_' + channel, source_name)

    def btn_fullscreen_clicked(self, btn):
        btn_name = btn.get_name()
        self.log.debug('btn_fullscreen_clicked: %s', btn_name)

        channel, idx = btn_name.split(' ')[:2]
        source_name = self.sources[int(idx)]

        self.log.info('selcting video %s for fullscreen', source_name)
        Connection.send('set_videos_and_composite',
                        source_name, '*', 'fullscreen')

    def on_video_status(self, source_a, source_b):
        self.log.info('on_video_status callback w/ sources: %s and %s',
                      source_a, source_b)

        self.current_source['a'] = source_a
        self.current_source['b'] = source_b

        self.a_btns[source_a].set_active(True)
        self.b_btns[source_b].set_active(True)
