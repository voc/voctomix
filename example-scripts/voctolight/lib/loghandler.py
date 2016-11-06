import logging
import time


class LogFormatter(logging.Formatter):

    def __init__(self, docolor, timestamps=False):
        super().__init__()
        self.docolor = docolor
        self.timestamps = timestamps

    def formatMessage(self, record):
        if self.docolor:
            c_lvl = 33
            c_mod = 32
            c_msg = 0

            if record.levelno == logging.WARNING:
                c_lvl = 31
                # c_mod = 33
                c_msg = 33

            elif record.levelno > logging.WARNING:
                c_lvl = 31
                c_mod = 31
                c_msg = 31

            fmt = ''.join([
                '\x1b[%dm' % c_lvl,  # set levelname color
                '%(levelname)8s',    # print levelname
                '\x1b[0m',           # reset formatting
                '\x1b[%dm' % c_mod,  # set name color
                ' %(name)s',         # print name
                '\x1b[%dm' % c_msg,  # set message color
                ': %(message)s',     # print message
                '\x1b[0m'            # reset formatting
            ])
        else:
            fmt = '%(levelname)8s %(name)s: %(message)s'

        if self.timestamps:
            fmt = '%(asctime)s ' + fmt

        if 'asctime' not in record.__dict__:
            record.__dict__['asctime'] = time.strftime(
                "%Y-%m-%d %H:%M:%S",
                time.localtime(record.__dict__['created'])
            )

        return fmt % record.__dict__


class LogHandler(logging.StreamHandler):

    def __init__(self, docolor, timestamps):
        super().__init__()
        self.setFormatter(LogFormatter(docolor, timestamps))
