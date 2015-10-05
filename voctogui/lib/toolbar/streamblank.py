import logging
from gi.repository import Gtk

import lib.connection as Connection

class StreamblankToolbarController(object):
	""" Manages Accelerators and Clicks on the Composition Toolbar-Buttons """

	def __init__(self, drawing_area, win, uibuilder, warning_overlay):
		self.log = logging.getLogger('StreamblankToolbarController')

		self.warning_overlay = warning_overlay

		blank_sources = ['pause', 'nostream']
		self.status_btns = {}

		livebtn = uibuilder.find_widget_recursive(drawing_area, 'stream_live')
		blankbtn = uibuilder.find_widget_recursive(drawing_area, 'stream_blank')

		blankbtn_pos = drawing_area.get_item_index(blankbtn)

		livebtn.connect('toggled', self.on_btn_toggled)
		livebtn.set_name('live')

		self.livebtn = livebtn
		self.blank_btns = {}

		for idx, name in enumerate(blank_sources):
			if idx == 0:
				new_btn = blankbtn
			else:
				new_icon = Gtk.Image.new_from_pixbuf(blankbtn.get_icon_widget().get_pixbuf())
				new_btn = Gtk.RadioToolButton(group=livebtn)
				new_btn.set_icon_widget(new_icon)
				drawing_area.insert(new_btn, blankbtn_pos+1)

			new_btn.set_label("Stream %s" % name)
			new_btn.connect('toggled', self.on_btn_toggled)
			new_btn.set_name(name)

			self.blank_btns[name] = new_btn

		# connect event-handler and request initial state
		Connection.on('stream_status', self.on_stream_status)
		Connection.send('get_stream_status')

	def on_btn_toggled(self, btn):
		if not btn.get_active():
			return

		btn_name = btn.get_name()
		self.log.info('stream-status activated: %s', btn_name)
		if btn_name == 'live':
			self.warning_overlay.disable()

		else:
			self.warning_overlay.enable(btn_name)

		if btn_name == 'live':
			Connection.send('set_stream_live')
		else:
			Connection.send('set_stream_blank', btn_name)

	def on_stream_status(self, status, source = None):
		self.log.info('on_stream_status callback w/ status %s and source %s', status, source)

		if status == 'live':
			self.livebtn.set_active(True)
		else:
			self.blank_btns[source].set_active(True)
