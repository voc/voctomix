from mock import ANY

from lib.response import NotifyResponse
from tests.commands.commands_test_base import CommandsTestBase


class SetAudioVolumeTest(CommandsTestBase):
    def test_set_audio_volume(self):
        response = self.commands.set_audio_volume("cam1", 0.75)
        self.pipeline_mock.amix.setAudioSourceVolume("cam1", 0.75)

        self.assertIsInstance(response, NotifyResponse)
        self.assertEqual(response.args, ('audio_status', ANY))

    def test_cant_set_audio_on_unknown_channel(self):
        with self.assertRaises(ValueError):
            self.commands.set_audio_volume("fooobar", 0.75)

        self.pipeline_mock.amix.setAudioSource.assert_not_called()

    def test_cant_set_audio_negative(self):
        with self.assertRaises(ValueError):
            self.commands.set_audio_volume("cam1", -5)

        self.pipeline_mock.amix.setAudioSource.assert_not_called()

    def test_cant_set_audio_on_int_channel(self):
        with self.assertRaises(ValueError):
            self.commands.set_audio_volume(1, 0.75)

        self.pipeline_mock.amix.setAudioSource.assert_not_called()
