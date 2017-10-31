from mock import MagicMock

from tests.helper.voctomix_test import VoctomixTest
from lib.config import Config
from lib.videomix import VideoMix, CompositeModes


class VideomixerSetCompositeMode(VoctomixTest):
    def setUp(self):
        super().setUp()
        self.videomixer = VideoMix()

        self.videomixer.getInputVideoSize = MagicMock(return_value=(42, 23))

        self.videomixer.setVideoSourceA = MagicMock()
        self.videomixer.setVideoSourceB = MagicMock()

    def test_can_set_composite_mode(self):
        Config.add_section('side-by-side-preview')

        self.videomixer.setCompositeMode(CompositeModes.side_by_side_preview)
        self.assertEqual(self.videomixer.compositeMode, CompositeModes.side_by_side_preview)

    def test_set_composite_mode_sets_default_a_source(self):
        Config.given('side-by-side-preview', 'default-a', 'cam1')

        self.videomixer.setCompositeMode(CompositeModes.side_by_side_preview)

        self.videomixer.setVideoSourceA.assert_called_with(0)
        self.videomixer.setVideoSourceB.assert_not_called()

    def test_set_composite_mode_sets_default_b_source(self):
        Config.given('side-by-side-preview', 'default-b', 'cam2')

        self.videomixer.setCompositeMode(CompositeModes.side_by_side_preview)

        self.videomixer.setVideoSourceA.assert_not_called()
        self.videomixer.setVideoSourceB.assert_called_with(1)

    def test_set_composite_mode_sets_default_a_and_b_source(self):
        Config.given('side-by-side-preview', 'default-a', 'grabber')
        Config.given('side-by-side-preview', 'default-b', 'cam1')

        self.videomixer.setCompositeMode(CompositeModes.side_by_side_preview)

        self.videomixer.setVideoSourceA.assert_called_with(2)
        self.videomixer.setVideoSourceB.assert_called_with(0)

    def test_set_composite_mode_does_not_set_default_source_if_requested(self):
        Config.given('side-by-side-preview', 'default-a', 'grabber')
        Config.given('side-by-side-preview', 'default-b', 'cam1')

        self.videomixer.setCompositeMode(CompositeModes.side_by_side_preview,
                                         apply_default_source=False)

        self.videomixer.setVideoSourceA.assert_not_called()
        self.videomixer.setVideoSourceB.assert_not_called()
