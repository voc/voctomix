from mock import MagicMock, ANY

from tests.helper.voctomix_test import VoctomixTest
from lib.commands import ControlServerCommands
from lib.videomix import CompositeModes


class CommandsSetVideosAndComposite(VoctomixTest):
    def setUp(self):
        super().setUp()
        self.pipeline_mock = MagicMock()

        self.commands = ControlServerCommands(self.pipeline_mock)

    def test_returns_expected_notifications(self):
        self.pipeline_mock.vmix.getCompositeMode.return_value = \
            CompositeModes.fullscreen

        self.pipeline_mock.vmix.getVideoSourceA.return_value = 0
        self.pipeline_mock.vmix.getVideoSourceB.return_value = 1

        notifications = self.commands.set_videos_and_composite(
            "cam1", "*", "*")

        self.assertContainsNotification(
            notifications, 'composite_mode', 'fullscreen')

        self.assertContainsNotification(
            notifications, 'video_status', 'cam1', 'cam2')

    def test_can_set_video_a(self):
        self.commands.set_videos_and_composite("cam1", "*", "*")

        self.pipeline_mock.vmix.setVideoSourceA.assert_called_with(0)
        self.pipeline_mock.vmix.setVideoSourceB.assert_not_called()
        self.pipeline_mock.vmix.setCompositeMode.assert_not_called()

    def test_cant_set_video_a_to_invalid_value(self):
        with self.assertRaises(IndexError):
            self.commands.set_videos_and_composite("foobar", "*", "*")

        self.pipeline_mock.vmix.setVideoSourceA.assert_not_called()
        self.pipeline_mock.vmix.setVideoSourceB.assert_not_called()

    def test_can_set_video_b(self):
        self.commands.set_videos_and_composite("*", "cam2", "*")

        self.pipeline_mock.vmix.setVideoSourceA.assert_not_called()
        self.pipeline_mock.vmix.setVideoSourceB.assert_called_with(1)
        self.pipeline_mock.vmix.setCompositeMode.assert_not_called()

    def test_cant_set_video_b_to_invalid_value(self):
        with self.assertRaises(IndexError):
            self.commands.set_videos_and_composite("*", "foobar", "*")

        self.pipeline_mock.vmix.setVideoSourceA.assert_not_called()
        self.pipeline_mock.vmix.setVideoSourceB.assert_not_called()

    def test_can_set_video_a_and_b(self):
        self.commands.set_videos_and_composite("cam2", "grabber", "*")

        self.pipeline_mock.vmix.setVideoSourceA.assert_called_with(1)
        self.pipeline_mock.vmix.setVideoSourceB.assert_called_with(2)
        self.pipeline_mock.vmix.setCompositeMode.assert_not_called()

    def test_cant_set_video_a_and_b_to_invalid_value(self):
        with self.assertRaises(IndexError):
            self.commands.set_videos_and_composite("foobar", "foobar", "*")

        self.pipeline_mock.vmix.setVideoSourceA.assert_not_called()
        self.pipeline_mock.vmix.setVideoSourceB.assert_not_called()

    def test_can_set_video_a_and_composite_mode(self):
        self.commands.set_videos_and_composite("cam2", "*", "fullscreen")

        self.pipeline_mock.vmix.setVideoSourceA.assert_called_with(1)
        self.pipeline_mock.vmix.setVideoSourceB.assert_not_called()
        self.pipeline_mock.vmix.setCompositeMode.assert_called_with(
            CompositeModes.fullscreen, apply_default_source=ANY)

    def test_can_set_video_b_and_composite_mode(self):
        self.commands.set_videos_and_composite(
            "*", "grabber", "side_by_side_equal")

        self.pipeline_mock.vmix.setVideoSourceA.assert_not_called()
        self.pipeline_mock.vmix.setVideoSourceB.assert_called_with(2)
        self.pipeline_mock.vmix.setCompositeMode.assert_called_with(
            CompositeModes.side_by_side_equal, apply_default_source=ANY)

    def test_can_set_video_a_and_b_and_composite_mode(self):
        self.commands.set_videos_and_composite(
            "cam1", "grabber", "side_by_side_equal")

        self.pipeline_mock.vmix.setVideoSourceA.assert_called_with(0)
        self.pipeline_mock.vmix.setVideoSourceB.assert_called_with(2)
        self.pipeline_mock.vmix.setCompositeMode.assert_called_with(
            CompositeModes.side_by_side_equal, apply_default_source=ANY)

    def test_can_set_composite_mode(self):
        self.commands.set_videos_and_composite(
            "*", "*", "side_by_side_preview")

        self.pipeline_mock.vmix.setVideoSourceA.assert_not_called()
        self.pipeline_mock.vmix.setVideoSourceB.assert_not_called()
        self.pipeline_mock.vmix.setCompositeMode.assert_called_with(
            CompositeModes.side_by_side_preview, apply_default_source=ANY)

    def test_setting_composite_mode_without_sources_applies_default_source(self):
        self.commands.set_videos_and_composite(
            "*", "*", "side_by_side_preview")

        self.pipeline_mock.vmix.setCompositeMode.assert_called_with(
            CompositeModes.side_by_side_preview, apply_default_source=True)


    def test_setting_composite_mode_with_a_source_does_not_apply_default_source(self):
        self.commands.set_videos_and_composite("grabber", "*", "fullscreen")

        self.pipeline_mock.vmix.setCompositeMode.assert_called_with(
            CompositeModes.fullscreen, apply_default_source=False)

    def test_setting_composite_mode_with_b_source_does_not_apply_default_source(self):
        self.commands.set_videos_and_composite("*", "grabber", "fullscreen")

        self.pipeline_mock.vmix.setCompositeMode.assert_called_with(
            CompositeModes.fullscreen, apply_default_source=False)

    def test_setting_composite_mode_with_a_and_b_source_does_not_apply_default_source(self):
        self.commands.set_videos_and_composite("cam1", "grabber", "fullscreen")

        self.pipeline_mock.vmix.setCompositeMode.assert_called_with(
            CompositeModes.fullscreen, apply_default_source=False)

    def assertContainsNotification(self, notifications, *args):
        self.assertTrue(
            any(n.args == args for n in notifications),
            msg="Expected notifications {} to contain '{}'".format(
                [str(n) for n in notifications],
                ' '.join(args)
            ))
