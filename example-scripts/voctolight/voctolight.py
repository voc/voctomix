#!/usr/bin/env python3
import socket
from lib.config import Config
from lib.plugins.all_plugins import get_plugin
import time


class TallyHandling:
    def __init__(self, plugin, source):
        self.plugin = plugin
        self.source = source
        self.state = None

    def set_state(self, state):
        self.state = state

    def video_change(self, source_a, source_b):
        if self.state == 'fullscreen':
            if source_a == self.source:
                self.plugin.tally_on()
            else:
                self.plugin.tally_off()
        else:
            if self.source in (source_a, source_b):
                self.plugin.tally_on()
            else:
                self.plugin.tally_off()


def start_connection(tally_handler):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

    sock.connect((Config.get('server', 'host'), 9999))
    sock.settimeout(None)

    print('Connected.')
    messages = []
    sock.send(b'get_composite_mode\n')
    sock.send(b'get_video\n')
    sock.send(b'get_stream_status\n')
    while True:
        if len(messages) == 0:
            message = sock.recv(2048)
            message = str(message, 'utf-8')

            if not message:
                start_connection(tally_handler)
                break
            messages = message.split('\n')

        message = messages[0].split()

        if len(messages) != 0:
            messages = messages[1:]
        try:
            if message[0] == 'composite_mode':
                tally_handler.set_state(message[1])
            elif message[0] == 'video_status':
                source_a, source_b = message[1], message[2]
                tally_handler.video_change(source_a, source_b)
        except IndexError:
            pass

def main():
    plugin = get_plugin(Config)
    tally_handler = TallyHandling(plugin, Config.get('light', 'cam'))
    try:
        while True:
            try:
                start_connection(tally_handler)
            except (TimeoutError, ConnectionRefusedError, socket.timeout):
                print('Connection error trying to reconnect in 1s.')
                time.sleep(1)
                continue
    finally:
        print('cleanup')

if __name__ in '__main__':
    main()
