#!/usr/bin/env python3
import re


class AudioStreams(list):

    def __init__(self):
        self = []

    def configure(cfg, source, use_soure_as_name=False):
        audio_streams = AudioStreams()

        # walk through all items within the configuration string
        for t_name, t in cfg:
            r = re.match(r'^audio.([\w\-_]+)$', t_name)
            if r:
                for i, channel in enumerate(t.split("+")):
                    audio_streams.add(AudioStream(
                        source, i, source if use_soure_as_name else r.group(1), channel))
        return audio_streams

    def add(self, audio_stream):
        self.append(audio_stream)

    def __str__(self):
        result = ""
        for index, audio_stream in enumerate(self):
            result += "mix.%d: %s.%d = %s.%d\n" % (
                index, audio_stream.name, audio_stream.channel, audio_stream.source, audio_stream.source_channel)
        return result

    def join(self, audio_streams):
        self += audio_streams

    def num_channels(self, source=None, grid=[x for x in range(0, 255)]):
        if source:
            result = 0
            for index, audio_stream in enumerate(self):
                if audio_stream.source == source:
                    result += 1
            while result not in grid:
                result += 1
            return result
        else:
            return len(self)

    def matrix(self, source, stream=None, grid=[x for x in range(0, 255)]):
        result = []
        for out, audio_stream in enumerate(self):
            row = []
            for ch in range(self.num_channels(source, grid)):
                row.append(1.0
                           if audio_stream.source == source
                           and audio_stream.source_channel == ch
                           and (stream is None or stream == audio_stream.name) else
                           0.0)
            result.append(row)
        return result

    def get_source_streams(self, source):
        result = {}
        for audio_stream in self:
            if source == audio_stream.source:
                if audio_stream.name not in result:
                    result[audio_stream.name] = []
                result[audio_stream.name].append(audio_stream)
        return result

    def get_stream_names(self, source=None):
        result = []
        for audio_stream in self:
            if not source or source == audio_stream.source:
                if audio_stream.name not in result:
                    result.append(audio_stream.name)
        return result


class AudioStream:
    def __init__(self, source, channel, name, source_channel):
        self.source = source
        self.channel = int(channel)
        self.name = name
        self.source_channel = int(source_channel)
