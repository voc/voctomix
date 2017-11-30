import unittest

from lib.errors.configuration_error import ConfigurationError
from tests.helper.voctomix_test import VoctomixTest
from lib.audiomix import AudioMix
from lib.videomix import VideoMix
from lib.config import Config


# noinspection PyUnusedLocal
class ExclusiveSources(VoctomixTest):

    def test_exclusive_sources(self):
        Config.given("mix", "audio_only", "cam2")
        Config.given("mix", "video_only", "grabber")
        audiomixer = AudioMix()
        videomixer = VideoMix()

        self.assertListEqual(audiomixer.names, ["cam1", "cam2"])
        self.assertListEqual(audiomixer.volumes, [1.0, 0.0])

        self.assertListEqual(videomixer.names, ["cam1", "grabber"])


if __name__ == '__main__':
    unittest.main()
