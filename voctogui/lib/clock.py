#!/usr/bin/python3
import logging
from gi.repository import Gst, GstNet

__all__ = ['Clock']
port = 9998

log = logging.getLogger('Clock')
Clock = None


def obtainClock(host):
    global log, Clock, SystemClock

    log.debug('obtaining NetClientClock from host %s', host)
    Clock = GstNet.NetClientClock.new('voctocore', host, port, 0)
    log.debug('obtained NetClientClock from host %s: %s', host, Clock)

    log.debug('waiting for NetClientClock to sync to host')
    Clock.wait_for_sync(Gst.CLOCK_TIME_NONE)
    log.info('successfully synced NetClientClock to host')
