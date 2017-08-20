import unittest

from lib.errors.configuration_error import ConfigurationError
from tests.helper.voctomix_test import VoctomixTest
from lib.audiomix import AudioMix
from lib.config import Config


# noinspection PyUnusedLocal
class AudiomixMultipleSources(VoctomixTest):
    def test_no_configured_audiosource_sets_first_to_full(self):
        audiomixer = AudioMix()

        self.assertListEqual(audiomixer.names, ["cam1", "cam2", "grabber"])
        self.assertListEqual(audiomixer.volumes, [1.0, 0.0, 0.0])

    def test_audiosource_sets_source_volume_to_full(self):
        Config.given("mix", "audiosource", "cam2")

        audiomixer = AudioMix()

        self.assertListEqual(audiomixer.names, ["cam1", "cam2", "grabber"])
        self.assertListEqual(audiomixer.volumes, [0.0, 1.0, 0.0])

    def test_per_source_volumes_set_volumes_to_configured_level(self):
        Config.given("source.cam1", "volume", "0.23")
        Config.given("source.cam2", "volume", "0.0")
        Config.given("source.grabber", "volume", "0.42")

        audiomixer = AudioMix()

        self.assertListEqual(audiomixer.names, ["cam1", "cam2", "grabber"])
        self.assertListEqual(audiomixer.volumes, [0.23, 0.0, 0.42])

    def test_audiosource_together_with_per_source_volumes_for_the_same_source_raises_an_error(self):
        Config.given("mix", "audiosource", "cam1")
        Config.given("source.cam1", "volume", "0.23")

        with self.assertRaises(ConfigurationError):
            audiomixer = AudioMix()

    def test_audiosource_together_with_per_source_volumes_for_different_sources_raises_an_error(self):
        Config.given("mix", "audiosource", "cam2")
        Config.given("source.cam1", "volume", "0.23")

        with self.assertRaises(ConfigurationError):
            audiomixer = AudioMix()

    def test_invalid_audiosource_raises_an_error(self):
        Config.given("mix", "audiosource", "camInvalid")

        with self.assertRaises(ConfigurationError):
            audiomixer = AudioMix()

    def test_configuring_audiosource_disables_ui_audio_selector(self):
        Config.given("mix", "audiosource", "cam1")

        audiomixer = AudioMix()
        self.assertEqual(Config.getboolean('audio', 'volumecontrol'), False)

    def test_configuring_per_source_volumes_disables_ui_audio_selector(self):
        Config.given("source.cam1", "volume", "1.0")

        audiomixer = AudioMix()
        self.assertEqual(Config.getboolean('audio', 'volumecontrol'), False)


if __name__ == '__main__':
    unittest.main()
