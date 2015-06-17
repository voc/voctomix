#!/usr/bin/python3
import gi, logging
from gi.repository import Gtk, Gst

from lib.uibuilder import UiBuilder

class Ui(UiBuilder):
	def __init__(self, uifile):
		self.log = logging.getLogger('Ui')
		super().__init__(uifile)

	def setup(self):
		# Aquire the Main-Window from the UI-File
		self.win = self.get_check_widget('window')

		# Connect Close-Handler
		self.win.connect('delete-event', Gtk.main_quit)

		self.configure_video_previews()
		self.configure_audio_selector()

	def configure_video_previews(self):
		sources = ['cam1', 'cam2', 'grabber']
		box = self.get_check_widget('box_left')

		for source in sources:
			preview = self.get_check_widget('widget_preview', clone=True)
			#box.add(preview)
			box.pack_start(preview, fill=False, expand=False, padding=0)

			# http://stackoverflow.com/questions/3489520/python-gtk-widget-name
			self.find_widget_recursive(preview, "label").set_label(source)

	def configure_audio_selector(self):
		combo = self.get_check_widget('combo_audio')
		combo.set_sensitive(True)

		liststore = self.get_check_widget('liststore_audio')
		liststore.clear()

		row = liststore.append()
		liststore.set(row, [0], ['foobar'])

		row = liststore.append('')
		liststore.set(row, [0], ['moofar'])

		combo.set_active_id('moofar')

	def show(self):
		self.win.show_all()
