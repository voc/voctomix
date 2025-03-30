from voctocore.lib.response import OkResponse
from voctocore.tests.commands.commands_test_base import CommandsTestBase


class GetStreamStatusTest(CommandsTestBase):
    def test_get_stream_status_blank(self):
        self.pipeline_mock.blinder.blind_source = 0
        response = self.commands.get_stream_status()

        self.assertIsInstance(response, OkResponse)
        self.assertEqual(response.args, ('stream_status', 'blinded', 'break'))

    def test_get_stream_status_live(self):
        self.pipeline_mock.blinder.blind_source = None
        response = self.commands.get_stream_status()

        self.assertIsInstance(response, OkResponse)
        self.assertEqual(response.args, ('stream_status', 'live'))
