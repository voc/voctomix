from typing import Protocol


class SystemdNotifier(Protocol):
    def notify(self, state: str) -> None:
        pass
