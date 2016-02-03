import logging
from gi.repository import Gtk

from lib.config import Config
import lib.connection as Connection


class MiscToolbarController(object):
	""" Manages Accelerators and Clicks Misc buttons """

	def __init__(self, drawing_area, win, uibuilder):
		self.log = logging.getLogger('MiscToolbarController')

		# Accelerators
		accelerators = Gtk.AccelGroup()
		win.add_accel_group(accelerators)

		closebtn = uibuilder.find_widget_recursive(drawing_area, 'close')
		closebtn.set_visible( Config.getboolean('misc', 'close') )
		closebtn.connect('clicked', self.on_closebtn_clicked)

		cutbtn = uibuilder.find_widget_recursive(drawing_area, 'cut')
		cutbtn.set_visible( Config.getboolean('misc', 'cut') )
		cutbtn.connect('clicked', self.on_cutbtn_clicked)

		key, mod = Gtk.accelerator_parse('t')
		cutbtn.add_accelerator('clicked', accelerators, key, mod, Gtk.AccelFlags.VISIBLE)

	def on_closebtn_clicked(self, btn):
		self.log.info('close-button clicked')
		Gtk.main_quit()

	def on_cutbtn_clicked(self, btn):
		self.log.info('cut-button clicked')
		Connection.send('message', 'cut')
