#!/usr/bin/env python3
import re

class AudioStreams:

    def __init__(self):
        self.audio_streams = []

    def configure(cfg, source):
        audio_streams = AudioStreams()

        # walk through all items within the configuration string
        for t_name, t in cfg:
            r = re.match(r'^audio.([\w\-_]+)$', t_name)
            if r:
                for i, channel in enumerate(t.split("+")):
                    audio_streams.add( AudioStream(source, i, r.group(1), channel) )
        return audio_streams

    def add(self, audio_stream):
        self.audio_streams.append(audio_stream)

    def __str__(self):
        result = ""
        for index, audio_stream in enumerate(self.audio_streams):
            result += "mix.%d: %s.%d = %s.%d\n" % (index, audio_stream.name, audio_stream.channel, audio_stream.source, audio_stream.source_channel)
        return result

    def join(self, audio_streams):
        self.audio_streams += audio_streams.audio_streams

    def num_channels(self, source=None, grid=[].extend(range(0,255))):
        if source:
            result = 0
            for index, audio_stream in enumerate(self.audio_streams):
                if audio_stream.source == source:
                    result += 1
            while result not in grid:
                result +=1
            return result
        else:
            return len(self.audio_streams)

    def matrix(self, source, grid=[].extend(range(0,255))):
        result = []
        for out, audio_stream in enumerate(self.audio_streams):
            row = []
            for ch in range(self.num_channels(source,grid)):
                row.append(1.0 if audio_stream.source == source and audio_stream.source_channel == ch else 0.0)
            result.append(row)
        return result

class AudioStream:
    def __init__(self, source, channel, name, source_channel):
        self.source = source
        self.channel = int(channel)
        self.name = name
        self.source_channel = int(source_channel)
