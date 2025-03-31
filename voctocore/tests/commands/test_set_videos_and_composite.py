import unittest
from unittest.mock import ANY, PropertyMock

import mock

from voctocore.lib.videomix import VideoMix
from voctocore.tests.commands.commands_test_base import CommandsTestBase
from voctocore.tests.mocks import args_mock
from voctocore.tests.mocks.config import config_mock


@mock.patch("voctocore.lib.videomix.Args", args_mock)
@mock.patch("voctocore.lib.videomix.Config", config_mock)
class CommandsSetVideosAndComposite(CommandsTestBase):
    @mock.patch("voctocore.lib.videomix.Args", args_mock)
    @mock.patch("voctocore.lib.videomix.Config", config_mock)
    def setUp(self):
        super().setUp()
        self.setCompositeEx = PropertyMock()
        self.pipeline_mock.vmix = VideoMix()
        self.pipeline_mock.vmix.setCompositeEx = self.setCompositeEx
        self.pipeline_mock.vmix.attach(self.pipeline_mock)
        self.setCompositeEx.reset_mock()

    def test_returns_expected_notifications(self):
        self.pipeline_mock.vmix.compositeMode = "fs"
        self.pipeline_mock.vmix.sourceA = "cam1"
        self.pipeline_mock.vmix.sourceB = "cam2"

        notifications = self.commands.set_videos_and_composite("cam1", "*", "*")

        self.assertContainsNotification(notifications, "composite_mode", "fs")
        self.assertContainsNotification(notifications, "video_status", "cam1", "cam2")

    def test_can_set_video_a(self):
        self.commands.set_videos_and_composite("cam1", "*", "*")
        self.setCompositeEx.assert_called_with(None, "cam1", None, ANY)

    @unittest.skip
    def test_cant_set_video_a_to_invalid_value(self):
        with self.assertRaises(ValueError):
            self.commands.set_videos_and_composite("foobar", "*", "*")
        self.setCompositeEx.assert_not_called()

    def test_can_set_video_b(self):
        self.commands.set_videos_and_composite("*", "cam2", "*")
        self.setCompositeEx.assert_called_with(None, None, "cam2", ANY)

    @unittest.skip
    def test_cant_set_video_b_to_invalid_value(self):
        with self.assertRaises(ValueError):
            self.commands.set_videos_and_composite("*", "foobar", "*")
        self.setCompositeEx.assert_not_called()

    def test_can_set_video_a_and_b(self):
        self.commands.set_videos_and_composite("cam2", "slides", "*")
        self.setCompositeEx.assert_called_with(None, "cam2", "slides", ANY)

    @unittest.skip
    def test_cant_set_video_a_and_b_to_invalid_value(self):
        with self.assertRaises(ValueError):
            self.commands.set_videos_and_composite("foobar", "foobar", "*")
        self.setCompositeEx.assert_not_called()

    def test_can_set_video_a_and_composite_mode(self):
        self.commands.set_videos_and_composite("cam2", "*", "fs")
        self.setCompositeEx.assert_called_with("fs", "cam2", None, ANY)

    def test_can_set_video_b_and_composite_mode(self):
        self.commands.set_videos_and_composite("*", "slides", "sbs")
        self.setCompositeEx.assert_called_with("sbs", None, "slides", ANY)

    def test_can_set_video_a_and_b_and_composite_mode(self):
        self.commands.set_videos_and_composite("cam1", "slides", "sbs")
        self.setCompositeEx.assert_called_with("sbs", "cam1", "slides", ANY)

    def test_can_set_composite_mode(self):
        self.commands.set_videos_and_composite("*", "*", "lec")
        self.setCompositeEx.assert_called_with("lec", None, None, ANY)
