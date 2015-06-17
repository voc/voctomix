#!/usr/bin/python3
import gi, logging
from gi.repository import Gtk, Gst

class UiBuilder(object):
	def __init__(self, uifile):
		self.log = logging.getLogger('UiBuilder')
		self.uifile = uifile

	def setup(self):
		self.builder = Gtk.Builder()
		self.builder.add_from_file(self.uifile)

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
			preview.get_children()[0].get_children()[0].get_children()[1].get_children()[0].set_label(source)

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

	def find_widget_recursive(self, widget_id, clone=False):
		pass

	def get_check_widget(self, widget_id, clone=False):
		if clone:
			builder = Gtk.Builder()
			builder.add_from_file(self.uifile)
		else:
			builder = self.builder

		self.log.debug('loading widget "%s" from the .ui-File', widget_id)
		widget = builder.get_object(widget_id)
		if not widget:
			self.log.error('could not load required widget "%s" from the .ui-File', widget_id)
			raise Exception('Widget not found in .ui-File')

		return widget
