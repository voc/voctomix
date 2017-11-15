import os.path
from configparser import SafeConfigParser

__all__ = ['get_config']


def get_config(filename=None):

    modulepath = os.path.dirname(os.path.realpath(__file__))

    files = [
        os.path.join(modulepath, '../default-config.ini'),
        os.path.join(modulepath, '../config.ini'),
        '/etc/voctomix/voctomidi.ini',
        '/etc/voctomidi.ini',
        os.path.expanduser('~/.voctomidi.ini'),
    ]

    if filename is not None:
        files.append(filename)

    Config = SafeConfigParser()
    Config.read(files)

    return Config
