from mock import ANY

from lib.response import NotifyResponse
from tests.commands.commands_test_base import CommandsTestBase


class SetVideoTest(CommandsTestBase):
    def test_set_video_a(self):
        response = self.commands.set_video_a("cam2")
        self.pipeline_mock.vmix.setVideoSourceA.assert_called_with(1)

        self.assertIsInstance(response, NotifyResponse)
        self.assertEqual(response.args, ('video_status', ANY, ANY))

    def test_cant_set_video_a_to_unknown_value(self):
        with self.assertRaises(ValueError):
            self.commands.set_video_a("foobar")

        self.pipeline_mock.vmix.setVideoSourceA.assert_not_called()

    def test_cant_set_video_a_to_int(self):
        with self.assertRaises(ValueError):
            self.commands.set_video_a(1)

        self.pipeline_mock.vmix.setVideoSourceA.assert_not_called()

    def test_set_video_b(self):
        response = self.commands.set_video_b("grabber")
        self.pipeline_mock.vmix.setVideoSourceB.assert_called_with(2)

        self.assertIsInstance(response, NotifyResponse)
        self.assertEqual(response.args, ('video_status', ANY, ANY))

    def test_cant_set_video_b_to_unknown_value(self):
        with self.assertRaises(ValueError):
            self.commands.set_video_b("moobar")

        self.pipeline_mock.vmix.setVideoSourceB.assert_not_called()

    def test_cant_set_video_b_to_int(self):
        with self.assertRaises(ValueError):
            self.commands.set_video_b(2)

        self.pipeline_mock.vmix.setVideoSourceB.assert_not_called()
