#!/usr/bin/python3
import gi, logging
from gi.repository import Gtk, Gst

class UiBuilder(Gtk.Builder):
	def __init__(self):
		self.log = logging.getLogger('UiBuilder')
		super().__init__()

	def setup(self):
		# Aquire the Main-Window from the UI-File
		self.log.debug('Loading Main-Window "window"  from .ui-File')
		self.win = self.get_check_widget("window")

		# Connect Close-Handler
		self.win.connect("delete-event", Gtk.main_quit)

	def show(self):
		self.win.show_all()

	def get_check_widget(self, widget_id):
		widget = self.get_object(widget_id)
		if not widget:
			self.log.error('could not load required widget "%s" from the .ui-File', widget_id)
			raise Exception('Widget not found in .ui-File')

		return widget
