#!/usr/bin/python3
import gi, signal, logging, sys

# import GStreamer and GLib-Helper classes
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject

# check min-version
minGst = (1, 5)
minPy = (3, 0)

if Gst.version() < minGst:
	raise Exception("GStreamer version", Gst.version(), 'is too old, at least', minGst, 'is required')

if sys.version_info < minPy:
	raise Exception("Python version", sys.version_info, 'is too old, at least', minPy, 'is required')


# init GObject & Co. before importing local classes
GObject.threads_init()
Gst.init([])

# import local classes
from lib.args import Args
from lib.pipeline import Pipeline
from lib.controlserver import ControlServer
from lib import notifications

# main class
class Voctocore(object):
	def __init__(self):
		self.log = logging.getLogger('Voctocore')
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
	logging.debug('initializing Voctocore')
	voctocore = Voctocore()

	notifications.controlserver = voctocore.controlserver

	logging.debug('running Voctocore')
	voctocore.run()

if __name__ == '__main__':
	main()
