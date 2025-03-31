#!/usr/bin/env python3
import re
import logging
from typing import Optional

log = logging.getLogger('AudioStreams')


class AudioStreams(list['AudioStream']):
    def __init__(self) -> None:
        super().__init__()

    def configure_source(self, cfg: list[tuple[str, str]], source: str, use_source_as_name: bool=False) -> None:
        """
        create an instance of <AudioStreams> for <source> that gets configured by INI section <cfg>
        If <use_source_as_name> is True items will be named as <source>.
        :param cfg:
        :param source:
        :param use_source_as_name:
        :return:
        """
        audiostreams: list['AudioStream'] = []
        # walk through all items within the configuration string
        for t_name, t in cfg:
            # search for entrys like 'audio.*'
            r = re.match(r'^audio\.([\w\-_]+)$', t_name)
            if r:
                for i, channel in enumerate(self.channels(t)):
                    name = source if use_source_as_name else r.group(1)
                    if self.has_stream(name):
                        log.error("input audio stream name '%s' can't be addressed a second time within source '%s'",
                                  name, source)
                    else:
                        audiostreams.append(AudioStream(source, i, name, channel))
        self.extend(audiostreams)

    @staticmethod
    def channels(channel_positions: str) -> list[str]:
        channels = []
        for entry in channel_positions.split("+"):
            if entry not in channels:
                channels.append(entry)
        return channels

    def has_stream(self, name: str, channel: Optional[int]=None) -> bool:
        for s in self:
            if s.name == name:
                if channel is None or s.channel == int(channel):
                    return True
        return False

    def __str__(self) -> str:
        result = ""
        for index, audio_stream in enumerate(self):
            result += "mix.%d: %s.%d = %s.%d\n" % (
                index, audio_stream.name, audio_stream.channel, audio_stream.source, audio_stream.source_channel)
        return result

    def source_channels(self, source: str) -> list[int]:
        """
        Return all audio channels by source.
        :param source:
        :return:
        """
        # collect source's channels into a set and count them
        return [audio_stream.source_channel for audio_stream in self if audio_stream.source == source]

    def num_channels(self, source, grid: list[int]=[x for x in range(0, 255)]):
        """
        Return the number of different audio channels overall or by source.
            Filter by <source> if given.
            Round up to values in <grid> to match external capabilities.
        :param source:
        :param grid:
        :return:
        """
        # collect source's channels into a set and count them
        channels = self.source_channels(source)
        result = max(channels) + 1 if channels else 0
        # fill up to values in grid
        while result not in grid:
            result += 1
        return result

    def matrix(self, source, stream=None, out_channels=None, grid: list[int]=[x for x in range(0, 255)]) -> list[list[float]]:
        """
        Return matrix that maps in to out channels of <source>.
            Filter by <stream> if given.
            Fill matrix up to <out_channel> rows if given.
            Round up number of matrix columns to values in <grid> to match
            external capabilities.
        :param source:
        :param stream:
        :param out_channels:
        :param grid:
        :return:
        """
        # collect result rows
        result: list[list[float]] = []
        for out, audio_stream in enumerate(self):
            row: list[float] = []
            # build result row based on number of channels in that source
            for ch in range(0, self.num_channels(source, grid)):
                # map source channels to out channels
                row.append(1.0 if audio_stream.source == source and audio_stream.source_channel == ch and (
                        stream is None or stream == audio_stream.name) else 0.0)
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

    def get_source_streams(self, source: str) -> dict[str, list['AudioStream']]:
        """
        filter all stream channels of given <source>
        :param source:
        :return:
        """
        result: dict[str, list[AudioStream]] = {}
        for audio_stream in self:
            if source == audio_stream.source:
                if audio_stream.name not in result:
                    result[audio_stream.name] = []
                result[audio_stream.name].append(audio_stream)
        return result

    def get_stream_names(self, source: Optional[str]=None) -> list[str]:
        """
        Get names of all streams.
            Filter by <source> if given.
        :param source:
        :return:
        """
        result: list[str] = []
        for audio_stream in self:
            if not source or source == audio_stream.source:
                if audio_stream.name not in result:
                    result.append(audio_stream.name)
        return result

    def get_stream_source(self, source: Optional[str]=None) -> list[str]:
        """
        Get sources of all streams.
                    Filter by <source> if given.
        :param source:
        :return:
        """
        result: list[str] = []
        for audio_stream in self:
            if not source or source == audio_stream.source:
                if audio_stream.name not in result:
                    result.append(audio_stream.source)
        return result


class AudioStream:
    source: str
    channel: int
    name: str
    source_channel: int

    def __init__(self, source: str, channel: int, name: str, source_channel: int):
        """
        initialize stream data
        :param source:
        :param channel:
        :param name:
        :param source_channel:
        """
        self.source = source
        self.channel = int(channel)
        self.name = name
        self.source_channel = int(source_channel)
