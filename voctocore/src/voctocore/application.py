"""
voctocore server application
"""

import sys
import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstNet', '1.0')
from gi.repository import Gst, GLib

from voctocore import cli
from voctocore import logging

logger = logging.getLogger(__name__)


def start():
    """Start the voctocore server"""
    args = cli.parse_args()

    Gst.init([])  # initialize library
    assert_requirements()

    # Bootstrap application
    logging.configure_from_args(args)

    app = Application()
    app.run()


class Application():
    """The voctocore main application"""
    def __init__(self):
        """Initialize application"""
        logger.debug('Creating GLib-MainLoop')
        self.mainloop = GLib.MainLoop()

    def run(self):
        """Run the main loop"""
        logger.info('Running. Waiting for connections....')
        try:
            self.mainloop.run()
        except KeyboardInterrupt:
            logger.info('Terminated via Ctrl-C')

    def quit(self):
        """Stop the main loop"""
        logger.info('Quitting.')
        self.mainloop.quit()


def assert_requirements():
    """Check if required system components are present"""
    min_gst = (1, 5)
    min_py = (3, 0)

    if Gst.version() < min_gst:
        raise Exception(
            "GStreamer version", Gst.version(),
            "is too old, at least", min_gst, "is required")

    if sys.version_info < min_py:
        raise Exception(
            "Python version", sys.version_info,
            "is too old, at least", min_py, "is required")


