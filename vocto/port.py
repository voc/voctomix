#!/usr/bin/env python3
import json


class Port(object):

    NONE = 0

    IN = 1
    OUT = 2

    def __init__(self, name, source=None):
        self.name = name
        if source:
            self.port = source.port()
            self.audio = source.audio_channels()
            self.video = source.video_channels()
            self.io = self.IN if source.is_input() else self.OUT

    def from_str(_str):
        p = Port(_str['name'])
        p.port = _str['port']
        p.audio = _str['audio']
        p.video = _str['video']
        p.io = _str['io']
        return p

    def is_input(self):
        return self.io == Port.IN

    def is_output(self):
        return self.io == Port.OUT
