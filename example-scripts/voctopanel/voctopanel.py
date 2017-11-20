#!/usr/bin/env python3
import atexit
import socket
import sys
import time
import serial

from lib.config import Config

server_address = Config.get("server", "address")
server_port = Config.get("server", "port")

panel_port = Config.get("panel", "port")
panel_speed = Config.get("panel", "speed")
panel_size = Config.get("panel", "size")

conn, ser = None, None

try:
    conn = socket.create_connection((server_address, server_port))
except (ConnectionRefusedError, KeyboardInterrupt):
    print("Could not connect to voctocore")
    sys.exit()

@atexit.register
def close_conn():
    global conn
    conn and conn.close()

try:
    ser = serial.Serial(panel_port, panel_speed, timeout=1)
except (ValueError, serial.SerialException):
    print("Could not connect to voctopanel")
    sys.exit()

@atexit.register
def close_pannel():
    global ser
    ser.close()

print("Entering main loop. Press Control-C to exit.")


try:
    # just wait for keyboard interrupt in main thread
    while True:
        if True: #ser.in_waiting > 0:
            try:
                btn = ser.readline().decode("utf-8").strip()
            except serial.serialutil.SerialException:
                print("probably missed one button press")

            #check if this is a button press and if it is remove the leading v
            if str(btn)[:1] == 'v':
                btn = btn[1:]
                try:
                    cm = Config.get("buttons",btn)
                except:
                    print("broken or not defined button received")
                print(cm) #debug

                print("Sending: '{}'".format(cm))
                try:
                    conn.sendall(cm.encode('ascii') + b"\n")
                except BrokenPipeError:
                    print("voctocore disconnected, trying to reconnect")
                    try:
                        conn = socket.create_connection((server_address, server_port))
                        print("Reconnected to voctocore")
                    except:
                        pass
                led = btn + 'o'
                ser.write(led.encode())

            else:
                pass
                #print(btn[:1])
        else:
            print('no input')
        #time.sleep(1)
except KeyboardInterrupt:
    print("")
