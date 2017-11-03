from lib.response import OkResponse
from tests.commands.commands_test_base import CommandsTestBase


class GetStreamStatusTest(CommandsTestBase):
    def test_get_stream_status_blank(self):
        self.pipeline_mock.streamblanker.blankSource = 1
        response = self.commands.get_stream_status()

        self.assertIsInstance(response, OkResponse)
        self.assertEqual(response.args, ('stream_status', 'blank', 'nostream'))

    def test_get_stream_status_live(self):
        self.pipeline_mock.streamblanker.blankSource = None
        response = self.commands.get_stream_status()

        self.assertIsInstance(response, OkResponse)
        self.assertEqual(response.args, ('stream_status', 'live'))
