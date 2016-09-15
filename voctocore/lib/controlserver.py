import socket
import logging
import traceback
from queue import Queue
from gi.repository import GObject

from lib.commands import ControlServerCommands
from lib.tcpmulticonnection import TCPMultiConnection
from lib.response import NotifyResponse, OkResponse


class ControlServer(TCPMultiConnection):

    def __init__(self, pipeline):
        '''Initialize server and start listening.'''
        self.log = logging.getLogger('ControlServer')
        super().__init__(port=9999)

        self.command_queue = Queue()

        self.commands = ControlServerCommands(pipeline)

    def on_accepted(self, conn, addr):
        '''Asynchronous connection listener.
           Starts a handler for each connection.'''
        self.log.debug('setting gobject io-watch on connection')
        GObject.io_add_watch(conn, GObject.IO_IN, self.on_data, [''])

    def on_data(self, conn, _, leftovers, *args):
        '''Asynchronous connection handler.
           Pushes data from socket into command queue linewise'''
        close_after = False
        try:
            while True:
                try:
                    leftovers.append(conn.recv(4096).decode(errors='replace'))
                    if len(leftovers[-1]) == 0:
                        self.log.info("Socket was closed")
                        leftovers.pop()
                        close_after = True
                        break

                except UnicodeDecodeError as e:
                    continue
        except:
            pass

        data = "".join(leftovers)
        del leftovers[:]

        lines = data.split('\n')
        for line in lines[:-1]:
            self.log.debug("got line: %r", line)

            line = line.strip()
            # 'quit' = remote wants us to close the connection
            if line == 'quit' or line == 'exit':
                self.log.info("Client asked us to close the Connection")
                self.close_connection(conn)
                return False

            self.log.debug('re-starting on_loop scheduling')
            GObject.idle_add(self.on_loop)

            self.command_queue.put((line, conn))

        if close_after:
            self.close_connection(conn)
            return False

        if lines[-1] != '':
            self.log.debug("remaining %r", lines[-1])

        leftovers.append(lines[-1])
        return True

    def on_loop(self):
        '''Command handler. Processes commands in the command queue whenever
        nothing else is happening (registered as GObject idle callback)'''

        self.log.debug('on_loop called')

        if self.command_queue.empty():
            self.log.debug('command_queue is empty again, '
                           'stopping on_loop scheduling')
            return False

        line, requestor = self.command_queue.get()

        words = line.split()
        if len(words) < 1:
            self.log.debug('command_queue is empty again, '
                           'stopping on_loop scheduling')
            return True

        command = words[0]
        args = words[1:]

        self.log.info("processing command %r with args %s", command, args)

        response = None
        try:
            # deny calling private methods
            if command[0] == '_':
                self.log.info('private methods are not callable')
                raise KeyError()

            command_function = self.commands.__class__.__dict__[command]

        except KeyError as e:
            self.log.info("received unknown command %s", command)
            response = "error unknown command %s\n" % command

        else:
            try:
                responseObject = command_function(self.commands, *args)

            except Exception as e:
                message = str(e) or "<no message>"
                response = "error %s\n" % message

            else:
                if isinstance(responseObject, NotifyResponse):
                    responseObject = [responseObject]

                if isinstance(responseObject, list):
                    for obj in responseObject:
                        signal = "%s\n" % str(obj)
                        for conn in self.currentConnections:
                            self._schedule_write(conn, signal)
                else:
                    response = "%s\n" % str(responseObject)

        finally:
            if response is not None and requestor in self.currentConnections:
                self._schedule_write(requestor, response)

        return False

    def _schedule_write(self, conn, message):
        queue = self.currentConnections[conn]

        self.log.debug('re-starting on_write[%u] scheduling', conn.fileno())
        GObject.io_add_watch(conn, GObject.IO_OUT, self.on_write)

        queue.put(message)

    def on_write(self, conn, *args):
        self.log.debug('on_write[%u] called', conn.fileno())

        try:
            queue = self.currentConnections[conn]
        except KeyError:
            return False

        if queue.empty():
            self.log.debug('write_queue[%u] is empty again, '
                           'stopping on_write scheduling',
                           conn.fileno())
            return False

        message = queue.get()
        try:
            conn.send(message.encode())
        except Exception as e:
            self.log.warn(e)

        return True

    def notify_all(self, msg):
        try:
            words = msg.split()
            words[-1] = self.commands.encodeSourceName(int(words[-1]))
            msg = " ".join(words) + '\n'
            for conn in self.currentConnections:
                self._schedule_write(conn, msg)
        except Exception as e:
            self.log.debug("error during notify: %s", e)
