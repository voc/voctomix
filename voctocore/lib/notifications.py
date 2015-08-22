#!/usr/bin/python3

# If you know a better way to do this, go for it...

import logging

log = logging.getLogger("Notifications")
controlserver = None

def notify_all(msg):
	try:
		controlserver.notify_all(msg)
	except Exception as e:
		log.warn(e)
