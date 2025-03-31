from typing import Iterable


class Response(object):
    args: Iterable[str]

    def __init__(self, *args):
        self.args = args

    def __str__(self) -> str:
        return " ".join(map(str, self.args))


class OkResponse(Response):
    pass


class NotifyResponse(Response):
    pass
