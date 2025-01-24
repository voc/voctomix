import logging
from queue import Empty, Queue
from threading import Lock

from gi.repository import GObject
from voctocore.lib.commands import ControlServerCommands
from voctocore.lib.response import NotifyResponse
from voctocore.lib.tcpmulticonnection import TCPMultiConnection

from vocto.port import Port


class ControlServer(TCPMultiConnection):

    def __init__(self, pipeline):
        '''Initialize server and start listening.'''
        self.log = logging.getLogger('ControlServer')
        super().__init__(port=Port.CORE_LISTENING)

        self.command_queue = Queue()

        self.on_loop_lock = Lock()
        self.on_loop_active = False

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
        except BlockingIOError:
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

            with self.on_loop_lock:
                if not self.on_loop_active:
                    self.log.debug('re-starting on_loop scheduling')
                    GObject.idle_add(self.on_loop)
                    self.on_loop_active = True

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

        with self.on_loop_lock:
            try:
                line, requestor = self.command_queue.get_nowait()
                self.log.debug(f'on_loop {line=} {requestor=}')
            except Empty:
                self.log.debug('command_queue is empty again, stopping on_loop scheduling')
                self.on_loop_active = False
                return False

        words = line.split()
        if len(words) < 1:
            self.log.debug(f'command_queue contained {line!r}, which is invalid, returning early')
            return True

        command = words[0]
        args = words[1:]
        self.log.debug(f"on_loop {command=} {args=}")

        response = None
        try:
            # deny calling private methods
            if command[0] == '_':
                self.log.info('Private methods are not callable')
                raise KeyError()

            command_function = self.commands.__class__.__dict__[command]
        except KeyError as e:
            self.log.info("Received unknown command %s", command)
            response = "error unknown command %s\n" % command

        else:
            try:
                responseObject = command_function(self.commands, *args)
            except Exception as e:
                self.log.error(f'{command}(*{args!r}) returned exception: {e!r}')
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
            self.log.debug(f'on_loop {response=} {requestor=}')
            if response is not None and requestor in self.currentConnections:
                self._schedule_write(requestor, response)

        return True

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

        try:
            message = queue.get_nowait()
            self.log.debug(f'on_write {message=}')
        except Empty:
            self.log.debug(f'write_queue[{conn.fileno()}] is empty again, stopping on_write scheduling')
            return False

        self.log.info("Responding message '%s'", message.strip())
        try:
            conn.send(message.encode())
        except Exception as e:
            self.log.warning("Failed to send message '%s'", message.encode(), exc_info=True)

        return True
