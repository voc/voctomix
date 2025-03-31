import logging
from abc import ABCMeta, abstractmethod

from gi.repository import Gst


class AVNode(object, metaclass=ABCMeta):
    bin: str
    pipeline: Gst.Pipeline

    @abstractmethod
    def attach(self, pipeline: Gst.Pipeline):
        pass

class AVIONode(AVNode, metaclass=ABCMeta):
    log: logging.Logger
    source: str

    @abstractmethod
    def port(self) -> str:
        pass

    @abstractmethod
    def num_connections(self) -> int:
        pass

    @abstractmethod
    def audio_channels(self) -> int:
        pass

    @abstractmethod
    def video_channels(self) -> int:
        pass

    @abstractmethod
    def is_input(self) -> bool:
        pass
