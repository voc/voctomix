import unittest

from lib.errors.configuration_error import ConfigurationError
from tests.helper.voctomix_test import VoctomixTest
from lib.audiomix import AudioMix
from lib.videomix import VideoMix
from lib.config import Config


# noinspection PyUnusedLocal
class ExclusiveSources(VoctomixTest):

    def test_exclusive_sources_not_in_both_types(self):
        Config.given("mix", "audio_only", "cam2")
        Config.given("mix", "video_only", "grabber")
        audiomixer = AudioMix()
        videomixer = VideoMix()

        self.assertListEqual(audiomixer.names, ["cam1", "cam2"])
        self.assertListEqual(audiomixer.volumes, [1.0, 0.0])

        self.assertListEqual(videomixer.names, ["cam1", "grabber"])

    def test_exclusive_sources_dont_accept_invalid_type(self):
        Config.given("mix", "audio_only", "cam2")
        Config.given("mix", "video_only", "grabber")
        audiomixer = AudioMix()
        videomixer = VideoMix()

        src_id = audiomixer.names.index("cam1")
        audiomixer.setAudioSource(src_id)
        # should succeed

        with self.assertRaises(ValueError):
            src_id = audiomixer.names.index("grabber")
            audiomixer.setAudioSource(src_id)
        # should fail

        src_id = videomixer.names.index("cam1")
        audiomixer.setAudioSource(src_id)
        # should succeed

        with self.assertRaises(ValueError):
            src_id = videomixer.names.index("cam2")
            audiomixer.setAudioSource(src_id)
        # should fail


if __name__ == '__main__':
    unittest.main()
