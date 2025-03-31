from voctocore.lib.response import OkResponse
from voctocore.tests.commands.commands_test_base import CommandsTestBase


class GetVideoTest(CommandsTestBase):
    def test_get_video(self):
        self.pipeline_mock.vmix.getVideoSources.return_value = ['cam1', 'cam2']

        response = self.commands.get_video()

        self.assertIsInstance(response, OkResponse)
        self.assertEqual(response.args, ('video_status', 'cam1', 'cam2'))
