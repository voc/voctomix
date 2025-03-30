from mock import ANY

from voctocore.lib.response import NotifyResponse
from voctocore.tests.commands.commands_test_base import CommandsTestBase


class SetStreamBlankerTest(CommandsTestBase):
    def setUp(self):
        super().setUp()

        def mock(src: int):
            self.pipeline_mock.blinder.blind_source = src

        self.pipeline_mock.blinder.setBlindSource.side_effect = mock

    def test_set_stream_blank(self):
        self.pipeline_mock.blinder.blind_source = None
        response = self.commands.set_stream_blank("break")
        self.pipeline_mock.blinder.setBlindSource.assert_called_with(0)

        self.assertIsInstance(response, NotifyResponse)
        self.assertEqual(response.args, ('stream_status', ANY, ANY))

    def test_cant_set_stream_blank_with_unknown_source(self):
        with self.assertRaises(ValueError):
            self.commands.set_stream_blank("foobar")

        self.pipeline_mock.blinder.setBlindSource.assert_not_called()

    def test_set_stream_live(self):
        self.pipeline_mock.blinder.blind_source = 0
        response = self.commands.set_stream_live()
        self.pipeline_mock.blinder.setBlindSource.assert_called_with(None)

        self.assertIsInstance(response, NotifyResponse)
        self.assertEqual(response.args, ('stream_status', 'live'))
