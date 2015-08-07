import logging
from gi.repository import Gtk

class CompositionToolbarController(object):
	""" Manages Accelerators and Clicks on the Composition Toolbar-Buttons """

	def __init__(self, drawing_area, win, uibuilder):
		self.log = logging.getLogger('CompositionToolbarController')

		accelerators = Gtk.AccelGroup()
		win.add_accel_group(accelerators)

		composites = [
			'composite-fullscreen',
			'composite-picture-in-picture',
			'composite-side-by-side-equal',
			'composite-side-by-side-preview'
		]

		for idx, name in enumerate(composites):
			key, mod = Gtk.accelerator_parse('F%u' % (idx+1))
			btn = uibuilder.find_widget_recursive(drawing_area, name)
			btn.set_name(name)

			# Thanks to http://stackoverflow.com/a/19739855/1659732
			btn.get_child().add_accelerator('clicked', accelerators, key, mod, Gtk.AccelFlags.VISIBLE)
			btn.connect('toggled', self.on_btn_toggled)

	def on_btn_toggled(self, btn):
		if not btn.get_active():
			return

		self.log.info("on_btn_toggled: %s", btn.get_name())
