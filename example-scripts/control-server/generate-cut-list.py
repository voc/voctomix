#!/usr/bin/env python3
import socket
import datetime
import sys

host = 'localhost'
port = 9999

conn = socket.create_connection((host, port))
fd = conn.makefile('rw')

for line in fd:
    words = line.rstrip('\n').split(' ')

    signal = words[0]
    args = words[1:]

    if signal == 'message' and args[0] == 'cut':
        ts = datetime.datetime.now().strftime("%Y-%m-%d/%H_%M_%S")
        print(ts)
        sys.stdout.flush()
