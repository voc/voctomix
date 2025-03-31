from unittest.mock import PropertyMock, MagicMock

import mock

from voctocore.lib.videomix import VideoMix
from voctocore.tests.helper.voctomix_test import VoctomixTest
from voctocore.tests.mocks import args_mock
from voctocore.tests.mocks.config import config_mock


@mock.patch("voctocore.lib.videomix.Args", args_mock)
@mock.patch("voctocore.lib.videomix.Config", config_mock)
class VideomixerSetSources(VoctomixTest):
    @mock.patch("voctocore.lib.videomix.Args", args_mock)
    @mock.patch("voctocore.lib.videomix.Config", config_mock)
    def setUp(self):
        super().setUp()
        self.videomixer = VideoMix()
        pipeline_mock = MagicMock()
        pipeline_mock.vmix = self.videomixer
        pipeline_mock.vmix.attach(pipeline_mock)

    def test_can_set_source_a(self):
        self.videomixer.setVideoSourceA("cam2")
        self.assertEqual(self.videomixer.sourceA, "cam2")

    def test_can_set_source_b(self):
        self.videomixer.setVideoSourceB("cam1")
        self.assertEqual(self.videomixer.sourceB, "cam1")

    def test_setting_source_a_swaps_a_and_b_if_required(self):
        self.videomixer.sourceA = "cam1"
        self.videomixer.sourceB = "cam2"

        self.videomixer.setVideoSourceA("cam2")

        self.assertEqual(self.videomixer.sourceA, "cam2")
        self.assertEqual(self.videomixer.sourceB, "cam1")

    def test_setting_source_b_swaps_a_and_b_if_required(self):
        self.videomixer.sourceA = "cam1"
        self.videomixer.sourceB = "cam2"

        self.videomixer.setVideoSourceB("cam1")

        self.assertEqual(self.videomixer.sourceA, "cam2")
        self.assertEqual(self.videomixer.sourceB, "cam1")
