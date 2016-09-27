import logging
import socket
import time
from gi.repository import GObject

from lib.config import Config


class TCPSingleConnection(object):

    def __init__(self, port):
        if not hasattr(self, 'log'):
            self.log = logging.getLogger('TCPSingleConnection')

        self.log.debug('Binding to Source-Socket on [::]:%u', port)
        self.boundSocket = socket.socket(socket.AF_INET6)
        self.boundSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.boundSocket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY,
                                    False)
        self.boundSocket.bind(('::', port))
        self.boundSocket.listen(1)

        self.currentConnection = None

        self.log.debug('Setting GObject io-watch on Socket')
        GObject.io_add_watch(self.boundSocket, GObject.IO_IN, self.on_connect)

    def on_connect(self, sock, *args):
        conn, addr = sock.accept()
        self.log.info('Incomming Connection from %s', addr)

        if self.currentConnection is not None:
            self.log.warn('Another Source is already connected, '
                          'closing existing pipeline')
            self.disconnect()
            time.sleep(1)

        self.on_accepted(conn, addr)
        self.currentConnection = conn

        return True

    def close_connection(self):
        self.currentConnection = None
        self.log.info('Connection closed')
