from mock import ANY

from lib.response import NotifyResponse
from tests.commands.commands_test_base import CommandsTestBase


class SetStreamBlankerTest(CommandsTestBase):
    def test_set_stream_blank(self):
        response = self.commands.set_stream_blank("pause")
        self.pipeline_mock.streamblanker.setBlankSource.assert_called_with(0)

        self.assertIsInstance(response, NotifyResponse)
        self.assertEqual(response.args, ('stream_status', ANY, ANY))

    def test_cant_set_stream_blank_with_unknown_source(self):
        with self.assertRaises(ValueError):
            self.commands.set_stream_blank("foobar")

        self.pipeline_mock.streamblanker.setBlankSource.assert_not_called()

    def test_set_stream_live(self):
        response = self.commands.set_stream_live()
        self.pipeline_mock.streamblanker.setBlankSource.assert_called_with(None)

        self.assertIsInstance(response, NotifyResponse)
        self.assertEqual(response.args, ('stream_status', ANY, ANY))
