from os import environ
import socket
from logging import getLogger

class SystemdNotify:
    def __init__(self):
        self.log = getLogger('SystemdNotify')

        addr = environ.get('NOTIFY_SOCKET')
        self.log.debug(f'{addr=}')
        if not addr:
            self.log.info('SD_NOTIFY not available')
            self.socket = None
            return

        self.log.info('SD_NOTIFY support enabled')
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        if addr[0] == '@':
            addr = '\0' + addr[1:]
        self.socket.connect(addr)

    def _send(self, msg):
        if not self.socket:
            # It's fine if we don't have a socket, that just means this
            # software was started without systemds 'Type=notify'
            self.log.debug(f'_send({msg!r}) called, but socket is not available')
            return

        self.log.info(msg)
        self.socket.sendall((msg.strip() + '\n').encode())

    def ready(self):
        self._send('READY=1')

    def reloading(self):
        self._send('RELOADING=1')

    def stopping(self):
        self._send('STOPPING=1')

    def status(self, msg):
        self._send(f'STATUS={msg}')


sd_notify = SystemdNotify()
