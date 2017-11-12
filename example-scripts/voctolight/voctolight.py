import socket
from lib.config import Config

DO_GPIO = True
try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BOARD)
except ModuleNotFoundError:
    DO_GPIO = False


class TallyHandling:

    def __init__(self, source, gpio_port):
        self.source = source
        self.state = ''
        self.stream_status = ''
        self.gpio_port = int(gpio_port)

    def set_state(self, state):
        self.state = state

    def set_stream_status(self, status):
        self.stream_status = status
        if status.split(' ')[0] == 'blank':
            self.tally_off()

    def tally_on(self):
        if DO_GPIO:
            GPIO.output(self.gpio_port, GPIO.HIGH)
        else:
            print('Tally on')

    def tally_off(self):
        if DO_GPIO:
            GPIO.output(self.gpio_port, GPIO.LOW)
        else:
            print('Tally off')

    def video_change(self, source_a, source_b):
        if self.stream_status == 'live':
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
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    try:
        sock.connect((Config.get('server', 'host'), 9999))
    except TimeoutError:
        start_connection(tally_handler)

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

        message = messages[0]

        if len(messages) != 0:
            messages = messages[1:]

        if message[:14] == 'composite_mode':
            tally_handler.set_state(message[15:])
        elif message[:12] == 'video_status':
            source_a, source_b = message[13:].split(' ')
            tally_handler.video_change(source_a, source_b)
        elif message[:13] == 'stream_status':
            status = message[14:]
            tally_handler.set_stream_status(status)
            if status == 'live':
                sock.send(b'get_video\n')


if __name__ in '__main__':
    tally_handler = TallyHandling(Config.get('light', 'cam'), Config.get('light', 'gpio_red'))
    start_connection(tally_handler)
