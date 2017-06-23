import logging
import socket
from queue import Queue
from abc import ABCMeta, abstractmethod
from gi.repository import GObject


class TCPMultiConnection(object, metaclass=ABCMeta):

    def __init__(self, port):
        if not hasattr(self, 'log'):
            self.log = logging.getLogger('TCPMultiConnection')

        self.boundSocket = None
        self.currentConnections = dict()

        self.log.debug('Binding to Source-Socket on [::]:%u', port)
        self.boundSocket = socket.socket(socket.AF_INET6)
        self.boundSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.boundSocket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY,
                                    False)
        self.boundSocket.bind(('::', port))
        self.boundSocket.listen(1)

        self.log.debug('Setting GObject io-watch on Socket')
        GObject.io_add_watch(self.boundSocket, GObject.IO_IN, self.on_connect)

    def on_connect(self, sock, *args):
        conn, addr = sock.accept()
        conn.setblocking(False)

        self.log.info("Incomming Connection from [%s]:%u (fd=%u)",
                      addr[0], addr[1], conn.fileno())

        self.currentConnections[conn] = Queue()
        self.log.info('Now %u Receiver connected',
                      len(self.currentConnections))

        self.on_accepted(conn, addr)

        return True

    def close_connection(self, conn):
        if conn in self.currentConnections:
            conn.close()
            del(self.currentConnections[conn])
        self.log.info('Now %u Receiver connected',
                      len(self.currentConnections))

    @abstractmethod
    def on_accepted(self, conn, addr):
        raise NotImplementedError(
            "child classes of TCPMultiConnection must implement on_accepted()"
        )
