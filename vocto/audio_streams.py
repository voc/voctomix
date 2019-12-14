#!/usr/bin/env python3
import re
import logging

log = logging.getLogger('AudioStreams')


class AudioStreams(list):

    def __init__(self):
        ''' just init the container '''
        self = []

    def configure(cfg, source, use_source_as_name=False):
        ''' create an instance of <AudioStreams> for <source> that gets configured by INI section <cfg>
            If <use_source_as_name> is True items will be named as <source>.
        '''
        audio_streams = AudioStreams()

        # walk through all items within the configuration string
        for t_name, t in cfg:
            # search for entrys like 'audio.*'
            r = re.match(r'^audio\.([\w\-_]+)$', t_name)
            if r:
                for i, channel in enumerate(t.split("+")):
                    audio_streams.append(AudioStream(source, i,
                                                     source if use_source_as_name else r.group(1), channel)
                                         )
        return audio_streams

    def __str__(self):
        result = ""
        for index, audio_stream in enumerate(self):
            result += "mix.%d: %s.%d = %s.%d\n" % (
                index, audio_stream.name, audio_stream.channel, audio_stream.source, audio_stream.source_channel)
        return result

    def source_channels(self, source):
        ''' Return all audio channels by source.
        '''
        # collect source's channels into a set and count them
        return [audio_stream.source_channel for audio_stream in self if audio_stream.source == source]

    def num_channels(self, source, grid=[x for x in range(0, 255)]):
        ''' Return the number of different audio channels overall or by source.
            Filter by <source> if given.
            Round up to values in <grid> to match external capabilities.
        '''
        # collect source's channels into a set and count them
        channels = self.source_channels(source)
        result = max(channels) + 1 if channels else 0
        # fill up to values in grid
        while result not in grid:
            result += 1
        return result

    def matrix(self, source, stream=None, out_channels=None, grid=[x for x in range(0, 255)]):
        ''' Return matrix that maps in to out channels of <source>.
            Filter by <stream> if given.
            Fill matrix up to <out_channel> rows if given.
            Round up number of matrix columns to values in <grid> to match
            external capabilities.
        '''
        # collect result rows
        result = []
        for out, audio_stream in enumerate(self):
            row = []
            # build result row based on number of channels in that source
            for ch in range(0, self.num_channels(source, grid)):
                # map source channels to out channels
                row.append(1.0
                           if audio_stream.source == source
                           and audio_stream.source_channel == ch
                           and (stream is None or stream == audio_stream.name) else
                           0.0)
            result.append(row)
        # if out channels are given
        if out_channels:
            # warn if source has more channels than out channels are given
            if out_channels < len(result):
                log.error("too many audio channels in source %s", source)
            else:
                # append rows up to out_channels
                result += [[0.0] *
                           self.num_channels(source, grid)] * (out_channels - len(result))
        return result

    def get_source_streams(self, source):
        ''' filter all stream channels of given <source> '''
        result = {}
        for audio_stream in self:
            if source == audio_stream.source:
                if audio_stream.name not in result:
                    result[audio_stream.name] = []
                result[audio_stream.name].append(audio_stream)
        return result

    def get_stream_names(self, source=None):
        ''' Get names of all streams.
            Filter by <source> if given.
        '''
        result = []
        for audio_stream in self:
            if not source or source == audio_stream.source:
                if audio_stream.name not in result:
                    result.append(audio_stream.name)
        return result

    def get_stream_source(self, source=None):
        ''' Get sources of all streams.
                    Filter by <source> if given.
                '''
        result = []
        for audio_stream in self:
            if not source or source == audio_stream.source:
                if audio_stream.name not in result:
                    result.append(audio_stream.source)
        return result

class AudioStream:
    def __init__(self, source, channel, name, source_channel):
        ''' initialize stream data '''
        self.source = source
        self.channel = int(channel)
        self.name = name
        self.source_channel = int(source_channel)
