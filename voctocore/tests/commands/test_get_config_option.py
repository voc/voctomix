import configparser
from lib.config import Config
from lib.response import OkResponse
from tests.commands.commands_test_base import CommandsTestBase


class GetConfigOptionTest(CommandsTestBase):
    def test_get_config_option(self):
        Config.given('somesection', 'somekey', 'somevalue')
        response = self.commands.get_config_option('somesection', 'somekey')

        self.assertIsInstance(response, OkResponse)
        self.assertEqual(response.args, ('server_config_option', 'somesection', 'somekey', 'somevalue'))

    def test_get_option_from_unknown_config_section_fails(self):
        with self.assertRaises(configparser.NoSectionError):
            self.commands.get_config_option('othersection', 'otherkey')

    def test_get_unknown_config_option_fails(self):
        Config.given('somesection', 'somekey', 'somevalue')

        with self.assertRaises(configparser.NoOptionError):
            self.commands.get_config_option('somesection', 'otherkey')
