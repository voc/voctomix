import logging
from gi.repository import Gtk

from lib.config import Config
import lib.connection as Connection

class MiscToolbarController(object):
	""" Manages Accelerators and Clicks Misc buttons """

	def __init__(self, drawing_area, win, uibuilder):
		self.log = logging.getLogger('MiscToolbarController')

		closebtn = uibuilder.find_widget_recursive(drawing_area, 'close')

		closebtn.connect('clicked', self.on_btn_clicked)

	def on_btn_clicked(self, btn):
		self.log.info('close-button clicked')
		Gtk.main_quit()
