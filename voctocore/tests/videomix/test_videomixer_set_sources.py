from tests.helper.voctomix_test import VoctomixTest
from lib.videomix import VideoMix


class VideomixerSetSources(VoctomixTest):
    def setUp(self):
        super().setUp()
        self.videomixer = VideoMix()

    def test_can_set_source_a(self):
        self.videomixer.setVideoSourceA(42)
        self.assertEqual(self.videomixer.sourceA, 42)

    def test_can_set_source_b(self):
        self.videomixer.setVideoSourceB(23)
        self.assertEqual(self.videomixer.sourceB, 23)

    def test_setting_source_a_swaps_a_and_b_if_required(self):
        self.videomixer.sourceA = 42
        self.videomixer.sourceB = 23

        self.videomixer.setVideoSourceA(23)

        self.assertEqual(self.videomixer.sourceA, 23)
        self.assertEqual(self.videomixer.sourceB, 42)

    def test_setting_source_b_swaps_a_and_b_if_required(self):
        self.videomixer.sourceA = 13
        self.videomixer.sourceB = 78

        self.videomixer.setVideoSourceB(13)

        self.assertEqual(self.videomixer.sourceA, 78)
        self.assertEqual(self.videomixer.sourceB, 13)
