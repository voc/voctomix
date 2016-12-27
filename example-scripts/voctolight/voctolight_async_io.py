#!/usr/bin/env python3

import asyncio
import configparser
import os.path
import json
import platform
from enum import Enum

try:
  import RPi.GPIO as GPIO
except ImportError:
  print("You need to be on a pi to make this work")

class Config(configparser.ConfigParser, object):
  config_files = [
    os.path.join(os.path.dirname(os.path.realpath(__file__)),
                 'default-config.ini'),
    os.path.join(os.path.dirname(os.path.realpath(__file__)),
                 'config.ini'),
    '/etc/voctomix/voctolight.ini',
    '/etc/voctolight.ini',
    os.path.expanduser('~/.voctolight.ini'),
  ]

  def __init__(self):
    super(Config,self).__init__()
    self.read(self.config_files)

  def setup_with_server_config(self, server_config):
    self.clear()
    self.read_dict(server_config)
    self.read(self.config_files)

  def getlist(self, section, option):
    return [x.strip() for x in self.get(section, option).split(',')]

class Connection(asyncio.Protocol):
  def __init__(self, interpreter):
    self.interpreter = interpreter

  def connect(self, host, port = 9999):
    self.loop = asyncio.get_event_loop()
    self.conn = self.loop.create_connection(lambda: self, host, port)
    self.loop.run_until_complete(conn.conn)

  def send(self, message):
    self.transport.write(message.encode())
    self.transport.write("\n".encode())

  def connection_made(self, transport):
    self.transport = transport

  def data_received(self, data):
#    print('data received: {}'.format(data.decode()))
    lines = data.decode().rstrip('\n').split('\n')
    for line in lines:
      interpreter.handler(line)

  def onnection_lost(self, exc):
    print('server closed the connection')
    asyncio.get_event_loop().stop()

### FIXME Duplicate from videomix.py
class CompositeModes(Enum):
    fullscreen = 0
    side_by_side_equal = 1
    side_by_side_preview = 2
    picture_in_picture = 3

class Interpreter(object):
  a_or_b = False
  composite_mode = CompositeModes.fullscreen

  def __init__(self, actor, config):
    self.config = config
    self.actor = actor
    actor.reset_led()

  def compute_state(self):
    if self.composite_mode == CompositeModes.fullscreen:
      actor.enable_tally(self.a_or_b and self.primary)
    else:   
      actor.enable_tally(self.a_or_b)

  def handler(self, response):
    words = response.split()
    signal = words[0]
    args = words[1:]
    try:
      self.__getattribute__("handle_"+signal)(args)
      interpreter.compute_state()
    except:
      print("Ignoring signal", signal)

  def handle_video_status(self, cams):
    mycam = self.config.get('light', 'cam')
    if mycam in cams:
      self.a_or_b = True
    else:
      self.a_or_b = False

    self.primary = (cams[0] == mycam)
#    print ("Is primary?", self.primary)

  def handle_composite_mode(self, mode_list):
    mode = mode_list[0]
    if mode == "fullscreen":
      self.composite_mode = CompositeModes.fullscreen
    elif mode == "side_by_side_equal":
      self.composite_mode = CompositeModes.side_by_side_equal
    elif mode == "side_by_side_preview":
      self.composite_mode = CompositeModes.side_by_side_preview
    else:
      print("Cannot handle", mode, "of type", type(mode))

  def handle_server_config(self, args):
    server_config_json = " ".join(args)
    server_config = json.loads(server_config_json)
    self.config.setup_with_server_config(server_config)


class LedActor:
  def __init__(self, config):
    self.gpios = config.get('light', 'gpios').split(',')
    self.gpio_red = int(config.get('light', 'gpio_red'))
    self.reset_led()

  def reset_led(self):
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)
    for gpio in self.gpios:
      gpio = int(gpio)
      GPIO.setup(gpio, GPIO.OUT)
      GPIO.output(gpio, GPIO.HIGH)

  def enable_tally(self, enable):
    if enable == True:
      GPIO.output(self.gpio_red, GPIO.LOW)
    else:
      GPIO.output(self.gpio_red, GPIO.HIGH)

class FakeLedActor:
  def __init__(self, config):
    pass

  def reset_led(self):
    print("LED has been reset to off")

  def enable_tally(self, enable):
    if enable == True:
      print("tally on!")
    else:
      print("tally off!")

if __name__ == "__main__":
  config = Config()
  if (platform.uname()[4] == 'armv7l'):
    actor = LedActor(config)
  else:
    actor = FakeLedActor(config)
  interpreter = Interpreter(actor, config)
  conn = Connection(interpreter)
  conn.connect(config.get('server', 'host'))
  conn.send("get_config")
  conn.send("get_composite_mode")
  conn.send("get_video")
  conn.loop.run_forever()
