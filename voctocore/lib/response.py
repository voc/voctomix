
class Response(object):

    def __init__(self, *args):
        self.args = args

    def __str__(self):
        return " ".join(map(str, self.args))


class OkResponse(Response):
    pass


class NotifyResponse(Response):
    pass
