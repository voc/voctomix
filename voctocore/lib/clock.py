#!/usr/bin/python3
import logging
from gi.repository import Gst, GstNet

__all__ = ['Clock', 'NetTimeProvider']
port = 9998

log = logging.getLogger('Clock')

log.debug("Obtaining System-Clock")
Clock = Gst.SystemClock.obtain()
log.info("Using System-Clock for all Pipelines: %s", Clock)

log.info("Starting NetTimeProvider on Port %u", port)
NetTimeProvider = GstNet.NetTimeProvider.new(Clock, '::', port)
