import logging
import socket
import time
from abc import ABCMeta, abstractmethod
from gi.repository import GObject


class TCPSingleConnection(object, metaclass=ABCMeta):

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
            self.log.warning('Another Source is already connected, '
                             'closing existing pipeline')
            self.disconnect()
            time.sleep(1)

        self.on_accepted(conn, addr)
        self.currentConnection = conn

        return True

    def close_connection(self):
        if self.currentConnection:
            self.currentConnection.close()
        self.currentConnection = None
        self.log.info('Connection closed')

    @abstractmethod
    def on_accepted(self, conn, addr):
        raise NotImplementedError(
            "child classes of TCPSingleConnection must implement on_accepted()"
        )

    @abstractmethod
    def disconnect(self):
        raise NotImplementedError(
            "child classes of TCPSingleConnection must implement disconnect()"
        )
