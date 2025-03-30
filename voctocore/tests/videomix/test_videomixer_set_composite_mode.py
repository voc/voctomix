from unittest.mock import PropertyMock

import mock
from mock import MagicMock

from voctocore.lib.videomix import VideoMix
from voctocore.tests.helper.voctomix_test import VoctomixTest
from voctocore.tests.mocks import args_mock
from voctocore.tests.mocks.config import config_mock


@mock.patch("voctocore.lib.videomix.Args", args_mock)
@mock.patch("voctocore.lib.videomix.Config", config_mock)
class VideomixerSetCompositeMode(VoctomixTest):
    @mock.patch("voctocore.lib.videomix.Args", args_mock)
    @mock.patch("voctocore.lib.videomix.Config", config_mock)
    def setUp(self):
        super().setUp()
        self.videomixer = VideoMix()
        pipeline_mock = MagicMock()
        pipeline_mock.vmix = self.videomixer
        pipeline_mock.vmix.attach(pipeline_mock)

    def test_can_set_composite_mode(self):
        self.videomixer.setCompositeMode("lec")
        self.assertEqual(self.videomixer.compositeMode, "lec")
