from mock import MagicMock

from voctocore.lib.pipeline import Pipeline
from voctocore.tests.helper.voctomix_test import VoctomixTest


class CommandsTestBase(VoctomixTest):
    def __init__(self, *args):
        super().__init__(*args)

    def setUp(self):
        super().setUp()
        self.pipeline_mock: Pipeline = MagicMock()
        from voctocore.lib.commands import ControlServerCommands
        self.commands = ControlServerCommands(self.pipeline_mock)

    def assertContainsNotification(self, notifications, *args):
        self.assertTrue(
            any(n.args == args for n in notifications),
            msg="Expected notifications {} to contain '{}'".format(
                [str(n) for n in notifications],
                ' '.join(args)
            ))
