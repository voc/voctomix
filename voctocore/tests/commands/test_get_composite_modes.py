from lib.response import OkResponse
from tests.commands.commands_test_base import CommandsTestBase


class GetCompositeModesTest(CommandsTestBase):
    def test_get_composite_modes(self):
        response = self.commands.get_composite_modes()

        self.assertIsInstance(response, OkResponse)
        self.assertEqual(response.args, (
            'composite_modes',
            'fullscreen,side_by_side_equal,side_by_side_preview,picture_in_picture'
        ))
