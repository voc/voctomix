import unittest
from unittest.mock import MagicMock

import mock

from voctocore.lib.audiomix import AudioMix
from voctocore.lib.config import Config
from voctocore.tests.helper.voctomix_test import VoctomixTest
from voctocore.tests.mocks import args_mock
from voctocore.tests.mocks.config import config_mock

@mock.patch("voctocore.lib.audiomix.Args", args_mock)
@mock.patch("voctocore.lib.audiomix.Config", config_mock)
class AudiomixMultipleSources(VoctomixTest):
    @mock.patch("voctocore.lib.audiomix.Args", args_mock)
    @mock.patch("voctocore.lib.audiomix.Config", config_mock)
    def setUp(self):
        super().setUp()
        self.audiomixer = AudioMix()
        pipeline_mock = MagicMock()
        pipeline_mock.amix = self.audiomixer
        pipeline_mock.amix.attach(pipeline_mock)

    def test_no_selected_audiosource_sets_all_to_full(self):
        self.assertListEqual(self.audiomixer.streams, ["cam1", "slides"])
        self.assertListEqual(self.audiomixer.volumes, [1.0, 1.0])

    def test_audiosource_sets_source_volume_to_full(self):
        self.audiomixer.volumes = [0.2, 0.2]

        self.audiomixer.setAudioSource(1)

        self.assertListEqual(self.audiomixer.streams, ["cam1", "slides"])
        self.assertListEqual(self.audiomixer.volumes, [0.0, 1.0])

    def test_per_source_volumes_set_volumes_to_configured_level(self):
        self.audiomixer.setAudioSourceVolume(0, 0.23)
        self.audiomixer.setAudioSourceVolume(1, 0.42)

        self.assertListEqual(self.audiomixer.streams, ["cam1", "slides"])
        self.assertListEqual(self.audiomixer.volumes, [0.23, 0.42])

    @unittest.skip
    def test_invalid_audiosource_raises_an_error(self):
        self.audiomixer.volumes = [0.2, 0.2]

        with self.assertRaises(ValueError):
            self.audiomixer.setAudioSource(5)

        self.assertListEqual(self.audiomixer.streams, ["cam1", "slides"])
        self.assertListEqual(self.audiomixer.volumes, [0.2, 0.2])

if __name__ == '__main__':
    unittest.main()
