#!/usr/bin/env python3
import json


class Port(object):

    NONE = 0

    IN = 1
    OUT = 2

    def __init__(self, name, source=None, audio=None, video=None):
        self.name = name
        self.source = source
        self.audio = audio
        self.video = video
        self.update()

    def todict(self):
        return {
            'name': self.name,
            'port': self.port,
            'audio': self.audio,
            'video': self.video,
            'io': self.io,
            'connections': self.connections
        }

    def update(self):
        if self.source:
            self.port = self.source.port()
            self.audio = self.source.audio_channels()
            self.video = self.source.video_channels()
            self.io = self.IN if self.source.is_input() else self.OUT
            self.connections = self.source.num_connections()

    def from_str(_str):
        p = Port(_str['name'])
        p.port = _str['port']
        p.audio = _str['audio']
        p.video = _str['video']
        p.io = _str['io']
        p.connections = _str['connections']
        return p

    def is_input(self):
        return self.io == Port.IN

    def is_output(self):
        return self.io == Port.OUT
