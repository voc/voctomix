import socket
import unittest

import gi.repository
from mock import MagicMock

import lib.config
from tests.helper.config_mock import ConfigMock

gi.repository.Gst = MagicMock()
gi.repository.GstNet = MagicMock()
gi.repository.GObject = MagicMock()
lib.config.Config = ConfigMock.WithBasicConfig()

socket.socket = MagicMock()


class VoctomixTest(unittest.TestCase):
    """Base-Class for all Voctomix-Tests"""

    def setUp(self):
        lib.config.Config.resetToDefaults()

    def assertContainsIgnoringWhitespace(self, text, search):
        regex = search.replace(" ", "\s*")

        try:
            self.assertRegex(text, regex)
        except AssertionError:
            raise AssertionError("search-string was out found in text (ignoring whitespace)\n"
                                 "search-string %s\n"
                                 "text:\n%s" % (search, text))
