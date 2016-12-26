import asyncio
from enum import Enum

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

  def __init__(self, actor):
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
    self.__getattribute__("handle_"+signal)(args)
    interpreter.compute_state()

  def handle_video_status(self, cams):
  ### FIXME DO NOT HARDCODE CAM NAME, READ FROM CONFIG!
    if "cam2" in cams:
      self.a_or_b = True
    else:
      self.a_or_b = False

    self.primary = (cams[0] == "cam2")
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


class FakeLedActor:
  def __init__(self):
    pass

  def reset_led(self):
    print("LED has been reset to off")

  def enable_tally(self, enable):
    if enable == True:
      print("tally on!")
    else:
      print("tally off!")

if __name__ == "__main__":
    actor = FakeLedActor()
    interpreter = Interpreter(actor)
    conn = Connection(interpreter)
    conn.connect("10.73.23.3")
    conn.send("get_composite_mode")
    conn.send("get_video")
    conn.loop.run_forever()
