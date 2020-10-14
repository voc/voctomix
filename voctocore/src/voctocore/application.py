"""
voctocore server application
"""

import sys

import sdnotify
import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstNet', '1.0')
from gi.repository import Gst, GLib

from voctocore import (
    cli,
    logging,
    configuration,
    pipeline,
)
from voctocore.ctrl.server import ControlServer

logger = logging.getLogger(__name__)


def start():
    """Start the voctocore server"""
    args = cli.parse_args()

    Gst.init([])  # initialize library
    assert_requirements()

    # Bootstrap application: Logging, Pipeline and Server
    logging.configure_from_args(args)
    logger.debug("Loading configuration")
    config = configuration.load_from_args(args)

    logger.debug("Creating A/V-Pipeline")
    pipeline = pipeline.from_config(config)

    logger.debug("Creating ControlServer")
    ctrl = ControlServer(pipeline)
    ctrl.start()

    # We are ready
    notify_systemd()

    # Start application main loop
    logger.debug('Creating GLib-MainLoop')
    main_loop = GLib.MainLoop()
    main_loop.run()


def notify_systemd():
    """Inform systemd that we started"""
    sdn = sdnotify.SystemdNotifier()
    sdn.notify("READY=1")


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


