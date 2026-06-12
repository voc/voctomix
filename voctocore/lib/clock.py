#!/usr/bin/python3
import logging
from gi.repository import Gst, GstNet

from vocto.port import Port

__all__ = ['Clock', 'NetTimeProvider']

log = logging.getLogger('Clock')

log.debug("Obtaining System-Clock")
Clock = Gst.SystemClock.obtain()
log.info("Using System-Clock for all pipelines.")

log.info("Starting NetTimeProvider on Port %u", Port.CLOCK)
NetTimeProvider = GstNet.NetTimeProvider.new(Clock, '::', Port.CLOCK)
