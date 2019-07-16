#!/usr/bin/env python3
import json


class Port(object):

    NONE = 0

    IN = 1
    OUT = 2

    OFFSET_PREVIEW = 100
    # input ports
    SOURCES_IN = 10000
    SOURCE_BACKGROUND = 16000
    SOURCE_OVERLAY= 14000
    SOURCES_BLANK = 17000
    AUDIO_SOURCE_BLANK = 18000
    # output ports
    MIX_OUT = 11000
    MIX_PREVIEW = MIX_OUT+OFFSET_PREVIEW
    SOURCES_OUT = 13000
    SOURCES_PREVIEW = SOURCES_OUT+OFFSET_PREVIEW
    LIVE_OUT = 15000
    LIVE_PREVIEW = LIVE_OUT+OFFSET_PREVIEW
    SLIDES_LIVE_OUT = 15001

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
