#!/usr/bin/python3
import gi, signal, logging, sys

# import GStreamer and GLib-Helper classes
gi.require_version('Gst', '1.0')
from gi.repository import GLib, Gst, GObject

# check min-version
minGst = (1, 4)
minPy = (3, 0)

if Gst.version() < minGst:
	raise Exception("GStreamer version", Gst.version(), 'is too old, at least', minGst, 'is required')

if sys.version_info < minPy:
	raise Exception("Python version", sys.version_info, 'is too old, at least', minPy, 'is required')


# init GObject before importing local classes
GObject.threads_init()
Gst.init(None)

# import local classes
from lib.pipeline import Pipeline
from lib.controlserver import ControlServer

# main class
class Voctocore:
	log = logging.getLogger('Voctocore')

	def __init__(self):
		self.log.debug('creating GObject-MainLoop')
		self.mainloop = GObject.MainLoop()

		# initialize subsystem
		self.log.debug('creating Video-Pipeline')
		self.pipeline = Pipeline()

		self.log.debug('creating ControlServer')
		self.controlserver = ControlServer(self.pipeline)
	
	def run(self):
		self.log.info('running Video-Pipeline')
		self.pipeline.run()

		self.log.info('running GObject-MainLoop')
		self.mainloop.run()

	def kill(self):
		self.log.info('quitting Video-Pipeline')
		self.pipeline.quit()

		self.log.info('quitting GObject-MainLoop')
		self.mainloop.quit()

	def on_eos(self, bus, msg):
		self.log.warning('received EOS-Signal on the Video-Bus from Element %s. This shouldn\'t happen if the program is not terminating right now', msg.src)
		self.kill()

	def on_error(self, bus, msg):
		err = msg.parse_error()
		self.log.error('received Error-Signal on the Video-Bus from Element %s: %s', msg.src, err[1])
		self.kill()


# run mainclass
def main(argv):
	# configure logging
	logging.basicConfig(level=logging.DEBUG,
		format='%(levelname)8s %(name)s: %(message)s')

	# make killable by ctrl-c
	logging.debug('setting SIGINT handler')
	signal.signal(signal.SIGINT, signal.SIG_DFL)

	# init main-class and main-loop
	logging.debug('initializing Voctocore')
	voctocore = Voctocore()

	logging.debug('running Voctocore')
	voctocore.run()

if __name__ == '__main__':
	main(sys.argv)
