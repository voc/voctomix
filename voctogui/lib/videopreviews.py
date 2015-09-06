import logging
from gi.repository import Gst, Gtk

from lib.config import Config
from lib.videodisplay import VideoDisplay

class VideoPreviewsController(object):
	""" Displays Video-Previews and selection Buttons for them """

	def __init__(self, drawing_area, win, uibuilder):
		self.log = logging.getLogger('VideoPreviewsController')

		self.drawing_area = drawing_area
		self.win = win

		self.sources = Config.getlist('mix', 'sources')
		self.preview_players = {}
		self.previews = {}

		try:
			width = Config.getint('previews', 'width')
			self.log.debug('Preview-Width configured to %u', width)
		except:
			width = 320
			self.log.debug('Preview-Width selected as %u', width)

		try:
			height = Config.getint('previews', 'height')
			self.log.debug('Preview-Height configured to %u', width)
		except:
			height = width*9/16
			self.log.debug('Preview-Height calculated to %u', width)

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
			drawing_area.pack_start(preview, fill=False, expand=False, padding=0)

			player = VideoDisplay(video, port=13000 + idx)

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

			key, mod = Gtk.accelerator_parse('%u' % (idx+1))
			btn_a.add_accelerator('activate', accelerators, key, mod, Gtk.AccelFlags.VISIBLE)

			key, mod = Gtk.accelerator_parse('<Ctrl>%u' % (idx+1))
			btn_b.add_accelerator('activate', accelerators, key, mod, Gtk.AccelFlags.VISIBLE)

			self.preview_players[source] = player
			self.previews[source] = preview

	def btn_toggled(self, btn):
		if not btn.get_active():
			return

		self.log.info('btn_toggled: %s', btn.get_name())
