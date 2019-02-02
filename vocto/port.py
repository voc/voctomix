#!/usr/bin/env python3
import json


class Port(object):

    NONE = 0

    IN = 1
    OUT = 2

    def __init__(self, name, port, audio, video, io):
        self.name = name
        self.port = port
        self.audio = audio
        self.video = video
        self.io = io

    def from_str(_str):
        return Port(_str['name'], _str['port'], _str['audio'], _str['video'], _str['io'])

    def is_input(self):
        return self.io == Port.IN

    def is_output(self):
        return self.io == Port.OUT
