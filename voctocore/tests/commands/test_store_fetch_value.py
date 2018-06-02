from mock import ANY

from lib.response import NotifyResponse, OkResponse
from tests.commands.commands_test_base import CommandsTestBase


class SetStoreFetchValueTest(CommandsTestBase):
    def test_store_value(self):
        response = self.commands.store_value('somekey', 'some-value')

        self.assertIsInstance(response, NotifyResponse)
        self.assertEqual(response.args, ('value', 'somekey', 'some-value'))

    def test_store_json_value(self):
        response = self.commands.store_value(
            'somekey',
            '{"json": ["rigid", "better for data interchange"]}')

        self.assertIsInstance(response, NotifyResponse)
        self.assertEqual(response.args, (
            'value',
            'somekey',
            '{"json": ["rigid", "better for data interchange"]}'
        ))

    def test_retrieve_value(self):
        self.commands.store_value('somekey', 'some-value')
        response = self.commands.fetch_value('somekey')

        self.assertIsInstance(response, OkResponse)
        self.assertEqual(response.args, ('value', 'somekey', 'some-value'))

    def test_latest_store_overwrites_value(self):
        self.commands.store_value('somekey', 'some-value')
        self.commands.store_value('somekey', 'another-value')
        response = self.commands.fetch_value('somekey')

        self.assertIsInstance(response, OkResponse)
        self.assertEqual(response.args, ('value', 'somekey', 'another-value'))

    def test_unknown_key_returns_empty_string(self):
        response = self.commands.fetch_value('otherkey')

        self.assertIsInstance(response, OkResponse)
        self.assertEqual(response.args, ('value', 'otherkey', ''))
