#!/usr/bin/python3
import gi, signal, logging, sys

# import GStreamer and GLib-Helper classes
gi.require_version('Gst', '1.0')
from gi.repository import Gtk, Gdk, Gst, GObject, GdkX11, GstVideo

# check min-version
minGst = (1, 4)
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
from lib.pipeline import Pipeline
from lib.controlserver import ControlServer

# main class
class Voctocore(object):
	log = logging.getLogger('Voctocore')

	def __init__(self):
		self.log.debug('creating GObject-MainLoop')
		self.mainloop = GObject.MainLoop()

		# initialize subsystem
		self.log.debug('creating A/V-Pipeline')
		self.pipeline = Pipeline()

		self.log.debug('creating ControlServer')
		self.controlserver = ControlServer(self.pipeline)

	def run(self):
		self.log.info('running GObject-MainLoop')
		try:
			self.mainloop.run()
		except KeyboardInterrupt:
			self.log.info('Terminated via Ctrl-C')

	def quit(self):
		self.log.info('quitting GObject-MainLoop')
		self.mainloop.quit()


# run mainclass
def main():
	# configure logging
	docolor = (Args.color == 'always') or (Args.color == 'auto' and sys.stderr.isatty())

	logging.basicConfig(
		level=logging.DEBUG if Args.verbose else logging.WARNING,
		format='\x1b[33m%(levelname)8s\x1b[0m \x1b[32m%(name)s\x1b[0m: %(message)s' if docolor else '%(levelname)8s %(name)s: %(message)s')

	# make killable by ctrl-c
	logging.debug('setting SIGINT handler')
	signal.signal(signal.SIGINT, signal.SIG_DFL)

	# init main-class and main-loop
	logging.debug('initializing Voctocore')
	voctocore = Voctocore()

	logging.debug('running Voctocore')
	voctocore.run()

if __name__ == '__main__':
	main()
