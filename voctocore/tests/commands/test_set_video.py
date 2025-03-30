import unittest
from unittest.mock import PropertyMock, ANY

import mock

from voctocore.lib.response import NotifyResponse
from voctocore.lib.videomix import VideoMix
from voctocore.tests.commands.commands_test_base import CommandsTestBase
from voctocore.tests.mocks import args_mock
from voctocore.tests.mocks.config import config_mock


@mock.patch("voctocore.lib.videomix.Args", args_mock)
@mock.patch("voctocore.lib.videomix.Config", config_mock)
class SetVideoTest(CommandsTestBase):
    @mock.patch("voctocore.lib.videomix.Args", args_mock)
    @mock.patch("voctocore.lib.videomix.Config", config_mock)
    def setUp(self):
        super().setUp()
        self.setCompositeEx = PropertyMock()
        self.pipeline_mock.vmix = VideoMix()
        self.pipeline_mock.vmix.setCompositeEx = self.setCompositeEx
        self.pipeline_mock.vmix.attach(self.pipeline_mock)
        self.setCompositeEx.reset_mock()

    def test_set_video_a(self):
        response = self.commands.set_video_a("cam2")
        self.setCompositeEx.assert_called_with(None, "cam2", None, useTransitions=ANY)

        self.assertIsInstance(response, NotifyResponse)
        self.assertEqual(response.args, ("video_status", ANY, ANY))

    def test_cant_set_video_a_to_unknown_value(self):
        with self.assertRaises(ValueError):
            self.commands.set_video_a("foobar")
        self.setCompositeEx.assert_not_called()

    def test_cant_set_video_a_to_int(self):
        with self.assertRaises(ValueError):
            self.commands.set_video_a(1)
        self.setCompositeEx.assert_not_called()

    def test_set_video_b(self):
        response = self.commands.set_video_b("slides")
        self.setCompositeEx.assert_called_with(None, None, "slides", useTransitions=ANY)

        self.assertIsInstance(response, NotifyResponse)
        self.assertEqual(response.args, ("video_status", ANY, ANY))

    def test_cant_set_video_b_to_unknown_value(self):
        with self.assertRaises(ValueError):
            self.commands.set_video_b("moobar")
        self.setCompositeEx.assert_not_called()

    def test_cant_set_video_b_to_int(self):
        with self.assertRaises(ValueError):
            self.commands.set_video_b(2)
        self.setCompositeEx.assert_not_called()
