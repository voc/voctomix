import unittest

import gi.repository
from mock import MagicMock

import lib.config
from tests.helper.config_mock import ConfigMock

gi.repository.Gst = MagicMock()
gi.repository.GstNet = MagicMock()
lib.config.Config = ConfigMock.WithBasicConfig()


class VoctomixTest(unittest.TestCase):
    """Base-Class for all Voctomix-Tests"""

    def setUp(self):
        lib.config.Config.resetToDefaults()
