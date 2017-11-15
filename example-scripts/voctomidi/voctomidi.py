#!/usr/bin/env python3
import argparse
import atexit
import socket
import sys
import time
from rtmidi.midiutil import open_midiport

from lib.config import get_config

NOTE_ON = 0x90
NOTE_OFF = 0x80
CC = 0xb0
VELOCITY = 0x7f


class MidiInputHandler(object):

    def __init__(self, host, port, feedback_mode, event_map):
        self.host = host
        self.port = port
        self.feedback_mode = feedback_mode

        self.source_a = None
        self.source_b = None
        self.cmode = None

        self.event_map = event_map

    def init(self, midi_device_name):

        self.conn = None
        self.midiin = None
        self.midiout = None

        try:
            self.conn = socket.create_connection((self.host, self.port))
        except (ConnectionRefusedError, KeyboardInterrupt):
            print("Could not connect to voctocore")
            sys.exit()

        @atexit.register
        def close_conn():
            self.conn and self.conn.close()

        try:
            self.midiin, self.midi_portname = open_midiport(midi_device_name)
        except (EOFError, KeyboardInterrupt):
            print("Opening midi port failed")
            sys.exit()

        @atexit.register
        def close_midi():
            self.midiin and self.midiin.close_port()

        self.midiin.set_callback(self.midiin_callback)

        if self.feedback_mode:
            try:
                self.midiout, _ = open_midiport(
                    midi_device_name,
                    type_='output'
                )
            except (EOFError, KeyboardInterrupt):
                print("Opening midi output port failed")
                sys.exit()

    def run(self):

        # get current mode on startup
        self.conn.send(b'get_video\r\n')
        self.conn.send(b'get_composite_mode\r\n')

        print("Entering main loop. Press Control-C to exit.")

        try:
            # read incoming socket, call `line_callback` line-buffered
            buf = b''
            while True:
                buf += self.conn.recv(1000000)
                lines = buf.split(b'\n')

                for l in lines[:-1]:
                    self.line_callback(l)
                buf = lines[-1]

        except KeyboardInterrupt:
            print("")

    def midiin_callback(self, event, data=None):
        message, _deltatime = event

        if message[0] == NOTE_OFF:
            self.update_interface()
            return

        elif message[0] == NOTE_ON:
            if message[1] in self.event_map:
                note = message[1]
                msg = "set_videos_and_composite " + self.event_map[note]
                print("Sending: '{}'".format(msg))
                try:
                    self.conn.sendall(msg.encode('ascii') + b"\n")
                except BrokenPipeError:
                    print("voctocore disconnected, trying to reconnect")
                    try:
                        self.conn = socket.create_connection(
                            (self.host, self.port)
                        )
                        print("Reconnected to voctocore")
                    except socket.error:
                        pass
            else:
                print("[{}]: Unhandled NOTE ON event {}".format(
                    self.midi_portname,
                    message[1])
                )

        else:
            print(repr(message))
            return

    def line_callback(self, line):
        tokens = line.split()

        if tokens[0] == b'video_status':
            self.source_a, self.source_b = tokens[1], tokens[2]
            self.update_interface()
        elif tokens[0] == b'composite_mode':
            self.cmode = tokens[1]
            self.update_interface()

    def update_interface(self):
        if not self.feedback_mode:
            return

        # reset all
        for note in self.event_map.keys():
            self.midiout.send_message([NOTE_OFF, note, VELOCITY])

        # set current mode
        for note, mode_string in self.event_map.items():
            sa, sb, cm = mode_string.encode().split()

            if sa == self.source_a \
                    and (sb == self.source_b or sb == b'*') \
                    and cm == self.cmode:
                self.midiout.send_message([NOTE_ON, note, VELOCITY])


def main():

    @atexit.register
    def kthxbye():
        print("Exit")

    parser = argparse.ArgumentParser(description='VoctoMIDI')
    parser.add_argument(
        '--config-file',
        default=None,
        help='Add another config file to the read list.'
    )
    args = parser.parse_args()

    Config = get_config(args.config_file)

    host = Config.get("server", "host")
    port = Config.get("server", "port", fallback=9999)
    feedback_mode = \
        Config.get("midi", "feedback", fallback="false").lower() == "true"

    midi_device_name = Config.get("midi", "device")

    event_map = {int(key): value for key, value in Config.items("eventmap")}

    mih = MidiInputHandler(host, port, feedback_mode, event_map)
    mih.init(midi_device_name)
    mih.run()


if __name__ == "__main__":
    main()
