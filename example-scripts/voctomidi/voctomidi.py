#!/usr/bin/env python3
import atexit
import socket
import sys
import time
from rtmidi.midiutil import open_midiport

from lib.config import Config

NOTE_ON = 144

host = Config.get("server", "host")
port = 9999

device = Config.get("midi", "device")

event_map = dict(map(lambda x: (int(x[0]), x[1]), Config.items("eventmap")))


class MidiInputHandler(object):

    def __init__(self, port):
        self.port = port

    def __call__(self, event, data=None):
        global conn
        message, _deltatime = event
        if message[0] != NOTE_ON:
            return
        if message[1] in event_map:
            note = message[1]
            msg = "set_videos_and_composite " + event_map[note]
            print("Sending: '{}'".format(msg))
            try:
                conn.sendall(msg.encode('ascii') + b"\n")
            except BrokenPipeError:
                print("voctocore disconnected, trying to reconnect")
                try:
                    conn = socket.create_connection((host, port))
                    print("Reconnected to voctocore")
                except socket.error:
                    pass
        else:
            print("[{}]: Unhandled NOTE ON event {}".format(self.port,
                                                            message[1]))


@atexit.register
def kthxbye():
    print("Exit")


conn, midiin = None, None

try:
    conn = socket.create_connection((host, port))
except (ConnectionRefusedError, KeyboardInterrupt):
    print("Could not connect to voctocore")
    sys.exit()


@atexit.register
def close_conn():
    global conn
    conn and conn.close()


try:
    midiin, port_name = open_midiport(device)
except (EOFError, KeyboardInterrupt):
    print("Opening midi port failed")
    sys.exit()


@atexit.register
def close_midi():
    global midiin
    midiin and midiin.close_port()
    del midiin


midiin.set_callback(MidiInputHandler(port_name))

print("Entering main loop. Press Control-C to exit.")
try:
    # just wait for keyboard interrupt in main thread
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("")
