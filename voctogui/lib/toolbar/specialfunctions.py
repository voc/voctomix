import logging
from gi.repository import Gtk

class SpecialFunctionsToolbarController(object):
	""" Manages Accelerators and Clicks on the Composition Toolbar-Buttons """

	def __init__(self, drawing_area, win, uibuilder, video_display):
		self.log = logging.getLogger('SpecialFunctionsToolbarController')

		self.video_display = video_display

		accelerators = Gtk.AccelGroup()
		win.add_accel_group(accelerators)

		composites = [
			'preview_fullscreen',
			'preview_freeze',
		]

		for idx, name in enumerate(composites):
			key, mod = Gtk.accelerator_parse('F%u' % (idx+10))
			btn = uibuilder.find_widget_recursive(drawing_area, name)
			btn.set_name(name)

			# Thanks to http://stackoverflow.com/a/19739855/1659732
			childbtn = btn.get_child()
			childbtn.add_accelerator('clicked', accelerators, key, mod, Gtk.AccelFlags.VISIBLE)
			childbtn.connect('button-press-event', self.on_btn_event)
			childbtn.connect('button-release-event', self.on_btn_event)

	def on_btn_event(self, btn, event):
		self.log.info("on_btn_event: %s @ %s", event.type, btn.get_name())
		# do sth. to self.video_display here
