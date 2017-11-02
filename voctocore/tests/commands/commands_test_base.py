from mock import MagicMock

from tests.helper.voctomix_test import VoctomixTest
from lib.commands import ControlServerCommands


class CommandsTestBase(VoctomixTest):
    def setUp(self):
        super().setUp()
        self.pipeline_mock = MagicMock()

        self.commands = ControlServerCommands(self.pipeline_mock)

    def assertContainsNotification(self, notifications, *args):
        self.assertTrue(
            any(n.args == args for n in notifications),
            msg="Expected notifications {} to contain '{}'".format(
                [str(n) for n in notifications],
                ' '.join(args)
            ))
