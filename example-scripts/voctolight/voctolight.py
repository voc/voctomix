#!/usr/bin/env python3
import socket
from lib.config import Config
import time

DO_GPIO = True
try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BOARD)
except ModuleNotFoundError:
    DO_GPIO = False


class TallyHandling:

    def __init__(self, source, gpio_port, all_gpios=()):
        self.source = source
        self.state = ''
        self.gpio_port = gpio_port
        if DO_GPIO:
            GPIO.setup(all_gpios, GPIO.OUT)
            GPIO.output(all_gpios, GPIO.HIGH)

    def set_state(self, state):
        self.state = state

    def tally_on(self):
        if DO_GPIO:
            GPIO.output(self.gpio_port, GPIO.LOW)
        print('Tally on')

    def tally_off(self):
        if DO_GPIO:
            GPIO.output(self.gpio_port, GPIO.HIGH)
        print('Tally off')

    def video_change(self, source_a, source_b):
        if self.state == 'fullscreen':
            if source_a == self.source:
                self.tally_on()
            else:
                self.tally_off()
        else:
            if self.source in (source_a, source_b):
                self.tally_on()
            else:
                self.tally_off()


def start_connection(tally_handler):

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

    sock.connect((Config.get('server', 'host'), 9999))
    sock.settimeout(None)

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


if __name__ in '__main__':
    try:
        all_gpios = Config.get('light', 'gpios').split(',')
        all_gpios = [int(i) for i in all_gpios]
        tally_handler = TallyHandling(Config.get('light', 'cam'), int(Config.get('light', 'gpio_red')),
                                      all_gpios=all_gpios)

        while True:
            try:
                start_connection(tally_handler)
            except (TimeoutError, ConnectionRefusedError, socket.timeout):
                print('Connection error trying to reconnect in 1s.')
                time.sleep(1)
                continue
    finally:
        print('cleanup')
        if DO_GPIO:
            GPIO.cleanup()
