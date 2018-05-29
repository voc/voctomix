from mock import ANY

from lib.response import NotifyResponse, OkResponse
from tests.commands.commands_test_base import CommandsTestBase


class SetStoreFetchMessageTest(CommandsTestBase):
    def test_store_message(self):
        response = self.commands.store_message('somekey', 'some-value')

        self.assertIsInstance(response, NotifyResponse)
        self.assertEqual(response.args, ('message', 'somekey', 'some-value'))

    def test_store_json_message(self):
        response = self.commands.store_message(
            'somekey',
            '{"json": ["rigid", "better for data interchange"]}')

        self.assertIsInstance(response, NotifyResponse)
        self.assertEqual(response.args, (
            'message',
            'somekey',
            '{"json": ["rigid", "better for data interchange"]}'
        ))

    def test_retrieve_message(self):
        self.commands.store_message('somekey', 'some-value')
        response = self.commands.fetch_message('somekey')

        self.assertIsInstance(response, OkResponse)
        self.assertEqual(response.args, ('message', 'somekey', 'some-value'))

    def test_latest_store_overwrites_message(self):
        self.commands.store_message('somekey', 'some-value')
        self.commands.store_message('somekey', 'another-value')
        response = self.commands.fetch_message('somekey')

        self.assertIsInstance(response, OkResponse)
        self.assertEqual(response.args, ('message', 'somekey', 'another-value'))

    def test_unknown_key_returns_empty_string(self):
        response = self.commands.fetch_message('otherkey')

        self.assertIsInstance(response, OkResponse)
        self.assertEqual(response.args, ('message', 'otherkey', ''))
