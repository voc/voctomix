import asyncio
from enum import Enum

class Connection(object):
  def __init__(self, interpreter):
    self.interpreter = interpreter 
    self.loop = asyncio.get_event_loop()

  def __del__(self):
    self.loop.close()

  def schedule(self, message):
    self.loop.create_task(self.connection_future(message, self.interpreter.handler))
   
  def set_host(self, host, port = '9999'):
    self.host = host
    self.port = port

  ### FIXME This logic is wrong. we must send requests, and independently wait for
  ### answers. Otherwise we will never receive answers to requests that we haven't
  ### asked for.
  @asyncio.coroutine
  def connection_future(connection, message, handler):
    reader, writer = yield from asyncio.open_connection(connection.host,
                                                        connection.port,
                                                        loop=connection.loop)
    print('Sent: %r' % message)
    writer.write(message.encode())
    writer.write('\n'.encode())
    data = yield from reader.readline()
    handler(message, data.decode().rstrip('\n'))
    writer.close()

### FIXME Duplicate from videomix.py
class CompositeModes(Enum):
    fullscreen = 0
    side_by_side_equal = 1
    side_by_side_preview = 2
    picture_in_picture = 3

class Interpreter(object):
  def __init__(self, actor):
    self.actor = actor
    self.a_or_b = False
    self.composite_mode = CompositeModes.fullscreen
    actor.reset_led()

  def compute_state(self):
    if self.composite_mode == CompositeModes.fullscreen:
      actor.enable_tally(self.a_or_b and self.primary)
    else:   
      actor.enable_tally(self.a_or_b)

  def handler(self, message, response):
    print("got " + response + " for " + message)
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
      

  def handle_composite_mode(self, mode):
    self.composite_mode = mode

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
    conn.set_host("10.73.23.3")
    conn.schedule("get_video")
    conn.schedule("get_composite_mode")
    conn.loop.run_forever()
    conn.wait_closed()
