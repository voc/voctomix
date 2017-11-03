from lib.response import OkResponse
from tests.commands.commands_test_base import CommandsTestBase


class GetVideoTest(CommandsTestBase):
    def test_get_video(self):
        self.pipeline_mock.vmix.getVideoSourceA.return_value = 0
        self.pipeline_mock.vmix.getVideoSourceB.return_value = 1

        response = self.commands.get_video()

        self.assertIsInstance(response, OkResponse)
        self.assertEqual(response.args, ('video_status', 'cam1', 'cam2'))
