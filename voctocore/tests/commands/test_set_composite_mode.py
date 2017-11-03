from mock import ANY

from lib.response import NotifyResponse
from lib.videomix import CompositeModes
from tests.commands.commands_test_base import CommandsTestBase


class SetCompositeModeTest(CommandsTestBase):
    def test_set_composite_mode(self):
        self.pipeline_mock.vmix.getCompositeMode.return_value = CompositeModes.side_by_side_equal

        response = self.commands.set_composite_mode("side_by_side_equal")
        self.pipeline_mock.vmix.setCompositeMode.assert_called_with(CompositeModes.side_by_side_equal)

        self.assertIsInstance(response[0], NotifyResponse)
        self.assertEqual(response[0].args[0], 'composite_mode')
        self.assertEqual(response[0].args, ('composite_mode', ANY))

        self.assertIsInstance(response[1], NotifyResponse)
        self.assertEqual(response[1].args, ('video_status', ANY, ANY))
