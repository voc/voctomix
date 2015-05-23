#!/usr/bin/python3
import gi, signal, logging, sys, os

# import GStreamer and GLib-Helper classes
gi.require_version('Gst', '1.0')
from gi.repository import Gtk, Gdk, Gst, GObject, GdkX11, GstVideo

# check min-version
minGst = (1, 5)
minPy = (3, 0)

if Gst.version() < minGst:
	raise Exception("GStreamer version", Gst.version(), 'is too old, at least', minGst, 'is required')

if sys.version_info < minPy:
	raise Exception("Python version", sys.version_info, 'is too old, at least', minPy, 'is required')


# init GObject & Co. before importing local classes
GObject.threads_init()
Gdk.init([])
Gtk.init([])
Gst.init([])

# import local classes
from lib.args import Args
from lib.uibuilder import UiBuilder

# main class
class Voctogui(object):
	def __init__(self):
		self.log = logging.getLogger('Voctogui')
		
		# Instanciate GTK-Builder
		self.builder = UiBuilder()

		# Uf a UI-File was specified on the Command-Line, load it
		if Args.ui_file:
			self.log.info('loading ui-file from file specified on command-line: %s', self.options.ui_file)
			self.builder.add_from_file(Args.ui_file)

		else:
			# Paths to look for the gst-switch UI-File
			paths = [
				os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ui/voctogui.ui'),
				'/usr/lib/voctogui/ui/voctogui.ui'
			]

			# Look for a gst-switch UI-File and load it
			for path in paths:
				self.log.debug('trying to load ui-file from file %s', path)

				if os.path.isfile(path):
					self.log.info('loading ui-file from file %s', path)
					self.builder.add_from_file(path)
					break

		self.builder.setup()


	def run(self):
		self.log.info('setting UI visible')
		self.builder.show()

		try:
			self.log.info('running Gtk-MainLoop')
			Gtk.main()
			self.log.info('Gtk-MainLoop ended')
		except KeyboardInterrupt:
			self.log.info('Terminated via Ctrl-C')

	def quit(self):
		self.log.info('quitting Gtk-MainLoop')
		Gtk.main_quit()


# run mainclass
def main():
	# configure logging
	docolor = (Args.color == 'always') or (Args.color == 'auto' and sys.stderr.isatty())

	if Args.verbose == 2:
		level = logging.DEBUG
	elif Args.verbose == 1:
		level = logging.INFO
	else:
		level = logging.WARNING

	if docolor:
		format = '\x1b[33m%(levelname)8s\x1b[0m \x1b[32m%(name)s\x1b[0m: %(message)s'
	else:
		format = '%(levelname)8s %(name)s: %(message)s'

	logging.basicConfig(level=level, format=format)

	# make killable by ctrl-c
	logging.debug('setting SIGINT handler')
	signal.signal(signal.SIGINT, signal.SIG_DFL)

	logging.info('Python Version: %s', sys.version_info)
	logging.info('GStreamer Version: %s', Gst.version())

	# init main-class and main-loop
	logging.debug('initializing Voctogui')
	voctogui = Voctogui()

	logging.debug('running Voctogui')
	voctogui.run()

if __name__ == '__main__':
	main()
