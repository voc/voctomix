import json
import logging
import socket
import sys
from queue import Queue

from gi.repository import GObject, Gtk

from vocto.port import Port

log = logging.getLogger('Connection')
conn = None
ip = None
command_queue = Queue()
signal_handlers = {}


def establish(host):
    global conn, log, ip

    log.info('establishing Connection to %s', host)
    try:
        conn = socket.create_connection((host, Port.CORE_LISTENING))
        log.info(
            "Connection to host %s at port %d successful" % (host, Port.CORE_LISTENING)
        )
    except ConnectionRefusedError:
        log.error(
            "Connecting to %s at port %d has failed. Is voctocore running? Can you ping the host?"
            % (host, Port.CORE_LISTENING)
        )
        sys.exit(-1)

    ip = conn.getpeername()[0]
    log.debug('Remote-IP is %s', ip)


def fetchServerConfig():
    global conn, log

    log.info('reading server-config')
    fd = conn.makefile('rw')
    fd.write("get_config\n")
    fd.flush()

    while True:
        line = fd.readline()
        words = line.split(' ')

        signal = words[0]
        args = words[1:]

        if signal != 'server_config':
            continue

        server_config_json = " ".join(args)
        server_config = json.loads(server_config_json)
        return server_config


def enterNonblockingMode():
    global conn, log

    log.debug('entering nonblocking-mode')
    conn.setblocking(False)
    GObject.io_add_watch(conn, GObject.IO_IN, on_data, [''])


def on_data(conn, _, leftovers, *args):
    global log

    '''Asynchronous connection handler. Pushes data from socket
    into command queue linewise'''
    try:
        while True:
            try:
                leftovers.append(conn.recv(4096).decode(errors='replace'))
                if len(leftovers[-1]) == 0:
                    log.info("Socket was closed")

                    # FIXME try to reconnect
                    conn.close()
                    Gtk.main_quit()
                    return False

            except UnicodeDecodeError as e:
                continue
    except BlockingIOError:
        pass

    data = "".join(leftovers)
    del leftovers[:]

    lines = data.split('\n')
    for line in lines[:-1]:
        log.debug("got line: %r", line)

        line = line.strip()
        log.debug('re-starting on_loop scheduling')
        GObject.idle_add(on_loop)

        command_queue.put((line, conn))

    if lines[-1] != '':
        log.debug("remaining %r", lines[-1])

    leftovers.append(lines[-1])
    return True


def on_loop():
    '''Command handler. Processes commands in the command queue whenever
    nothing else is happening (registered as GObject idle callback)'''

    global command_queue

    log.debug('on_loop called')

    if command_queue.empty():
        log.debug('command_queue is empty again, stopping on_loop scheduling')
        return False

    line, requestor = command_queue.get()

    words = line.split()
    if len(words) < 1:
        log.debug('command_queue is empty again, stopping on_loop scheduling')
        return True

    signal = words[0]
    args = words[1:]
    log.debug(f"on_loop {signal=} {args=}")
    if signal == "error":
        log.error('received error: %s', line)
    if signal not in signal_handlers:
        return True

    for handler in signal_handlers[signal]:
        handler(*args)

    return True


def send(command, *args):
    global conn, log
    if len(args) > 0:
        command += ' ' + (' '.join(args))

    command += '\n'

    conn.send(command.encode('ascii'))


def on(signal, cb):
    if signal not in signal_handlers:
        signal_handlers[signal] = []

    signal_handlers[signal].append(cb)
