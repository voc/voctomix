from mock import ANY

from vocto.composite_commands import CompositeCommand
from voctocore.lib.response import NotifyResponse
from voctocore.tests.commands.commands_test_base import CommandsTestBase


class SetCompositeModeTest(CommandsTestBase):
    def test_set_composite_mode(self):
        self.pipeline_mock.vmix.getCompositeMode.return_value = 'sbs'

        response = self.commands.set_composite_mode("sbs")
        self.pipeline_mock.vmix.setComposite.assert_called_with(CompositeCommand('sbs', "*", "*"))

        self.assertIsInstance(response[0], NotifyResponse)
        self.assertEqual(response[0].args[0], 'composite_mode')
        self.assertEqual(response[0].args, ('composite_mode', ANY))

        self.assertIsInstance(response[1], NotifyResponse)
        self.assertEqual(response[1].args, ('video_status',))
