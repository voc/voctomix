#!/usr/bin/python3
import gi, logging
from gi.repository import Gtk, Gst

from lib.config import Config
from lib.uibuilder import UiBuilder
from lib.videodisplay import VideoDisplay

class Ui(UiBuilder):
	def __init__(self, uifile):
		self.log = logging.getLogger('Ui')
		super().__init__(uifile)

	def setup(self):
		# Aquire the Main-Window from the UI-File
		self.win = self.get_check_widget('window')

		# Connect Close-Handler
		self.win.connect('delete-event', Gtk.main_quit)

		self.previews = {}
		self.preview_players = {}

		self.configure_video_main()
		self.configure_video_previews()
		self.configure_audio_selector()

	def configure_video_main(self):
		video = self.find_widget_recursive(self.win, 'video_main')
		audiolevel = self.find_widget_recursive(self.win, 'audiolevel_main')
		self.video_main_player = VideoDisplay(11000, video, audiolevel, playaudio=True)

	def configure_video_previews(self):
		sources = ['cam1', 'cam2', 'grabber']
		box = self.find_widget_recursive(self.win, 'box_left')

		for idx, source in enumerate(sources):
			preview = self.get_check_widget('widget_preview', clone=True)
			video = self.find_widget_recursive(preview, 'video')

			try:
				width = Config.getint('previews', 'width')
			except:
				width = 320

			try:
				height = Config.getint('previews', 'height')
			except:
				height = width*9/16

			video.set_size_request(width, height)

			box.pack_start(preview, fill=False, expand=False, padding=0)

			# http://stackoverflow.com/questions/3489520/python-gtk-widget-name
			self.find_widget_recursive(preview, 'label').set_label(source)

			player = VideoDisplay(13000 + idx, video)

			self.preview_players[source] = player
			self.previews[source] = preview

	def configure_audio_selector(self):
		combo = self.find_widget_recursive(self.win, 'combo_audio')
		combo.set_sensitive(True)

		# FIXME access via combo_audio?
		liststore = self.get_check_widget('liststore_audio')
		liststore.clear()

		row = liststore.append()
		liststore.set(row, [0], ['foobar'])

		row = liststore.append('')
		liststore.set(row, [0], ['moofar'])

		combo.set_active_id('moofar')

	def show(self):
		self.video_main_player.run()
		for name, player in self.preview_players.items():
			player.run()

		self.win.show_all()
