from abc import ABC, abstractmethod

__all__ = ['BasePlugin']


class BasePlugin(ABC):
    """An abstract plugin class, that all other plugins inherit from."""

    def __init__(self, config):
        ...

    @abstractmethod
    def tally_on(self) -> None:
        """Called when the tally light should be turned on."""
        ...

    @abstractmethod
    def tally_off(self) -> None:
        """Called when the tally light should be turned off."""
        ...
