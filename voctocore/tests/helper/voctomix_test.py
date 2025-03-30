import unittest

import voctocore.lib.config
from voctocore.tests.mocks.config import config_mock


class VoctomixTest(unittest.TestCase):
    def __init__(self, *args):
        super().__init__(*args)
        voctocore.lib.config.Config = config_mock

    """Base-Class for all Voctomix-Tests"""

    def setUp(self):
        config_mock.resetToDefaults()

    def assertContainsIgnoringWhitespace(self, text, search):
        regex = search.replace(" ", r"\s*")

        try:
            self.assertRegex(text, regex)
        except AssertionError:
            raise AssertionError("search-string was out found in text (ignoring whitespace)\n"
                                 "search-string %s\n"
                                 "text:\n%s" % (search, text))
