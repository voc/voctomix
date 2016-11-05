#!/usr/bin/env python3
import atexit
import sys
import time
import RPi.GPIO as GPIO
import lib.connection as Connection
from lib.config import Config

server_address = Config.get("server", "address")
server_port = Config.get("server", "port")

panel_port = Config.get("panel", "port")
panel_speed = Config.get("panel", "speed")
panel_size = Config.get("panel", "size")

conn, ser = None, None

GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.OUT)

Connection.establish(server_address)

# fetch config from server
Config.fetchServerConfig()

# switch connection to nonblocking, event-driven mode
Connection.enterNonblockingMode()

print("Entering main loop. Press Control-C to exit.")


try:
    # just wait for keyboard interrupt in main thread
    while True:

except KeyboardInterrupt:
    print("")
