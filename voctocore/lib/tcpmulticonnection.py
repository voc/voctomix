import logging
import socket
import sys
from queue import Queue
from abc import ABCMeta, abstractmethod
from gi.repository import GObject

from typing import Optional


class TCPMultiConnection(metaclass=ABCMeta):
    log: logging.Logger
    _port: Optional[int]
    boundSocket: Optional[socket.socket]
    currentConnections: dict[socket.socket, Queue]

    def __init__(self, port: int):
        if not hasattr(self, 'log'):
            self.log = logging.getLogger('TCPMultiConnection')

        self._port = None

        try:
            self.boundSocket = None
            self.currentConnections = dict()

            self.log.debug('Binding to Source-Socket on [::]:%u', port)
            self.boundSocket = socket.socket(socket.AF_INET6)
            self.boundSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.boundSocket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY,
                                        False)
            self.boundSocket.bind(('::', port))
            self.boundSocket.listen(1)
            self._port = port

            self.log.debug('Setting GObject io-watch on Socket')
            GObject.io_add_watch(self.boundSocket, GObject.IO_IN, self.on_connect)
        except OSError:
            self.log.error("Can not open listening port %d because it is already in use. Is another instance of voctocore running already?" % port)
            sys.exit(-1)


    def port(self) -> str:
        return "%s:%d" % (socket.gethostname(), self._port if self._port else 0)

    def num_connections(self) -> int:
        return len(self.currentConnections)

    def _log_num_connections(self):
        # lives in its own method so we can overwrite it in children
        self.log.info(f'Now {self.num_connections()} Receiver(s) connected')

    def is_input(self) -> bool:
        return False

    def on_connect(self, sock: socket.socket, *args):
        conn, addr = sock.accept()
        conn.setblocking(False)

        self.log.info("Incoming Connection from [%s]:%u (fd=%u)",
                      addr[0], addr[1], conn.fileno())

        self.currentConnections[conn] = Queue()
        self._log_num_connections()

        self.on_accepted(conn, addr)

        return True

    def close_connection(self, conn: socket.socket):
        if conn in self.currentConnections:
            conn.close()
            del(self.currentConnections[conn])
        self._log_num_connections()

    @abstractmethod
    def on_accepted(self, conn: socket.socket, addr: tuple[str, int]):
        raise NotImplementedError(
            "child classes of TCPMultiConnection must implement on_accepted()"
        )
