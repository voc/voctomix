#!/usr/bin/python3
import logging
from gi.repository import Gst, GstNet

__all__ = ['Clock']
port = 9998

log = logging.getLogger('Clock')
Clock = None

log.debug("Obtaining System-Clock")
SystemClock = Gst.SystemClock.obtain()

def obtainClock(host):
	global log, Clock, SystemClock

	log.debug('obtaining NetClientClock from host %s', host)
	Clock = GstNet.NetClientClock.new('voctocore', host, port, SystemClock.get_time())
	log.info('obtained NetClientClock from host %s: %s', host, Clock)
