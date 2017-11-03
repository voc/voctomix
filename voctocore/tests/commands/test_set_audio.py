from mock import ANY

from lib.response import NotifyResponse
from tests.commands.commands_test_base import CommandsTestBase


class SetAudioTest(CommandsTestBase):
    def test_set_audio(self):
        response = self.commands.set_audio("grabber")
        self.pipeline_mock.amix.setAudioSource.assert_called_with(2)

        self.assertIsInstance(response, NotifyResponse)
        self.assertEqual(response.args, ('audio_status', ANY))

    def test_cant_set_audio_to_unknown_value(self):
        with self.assertRaises(ValueError):
            self.commands.set_audio("moofoo")

        self.pipeline_mock.amix.setAudioSource.assert_not_called()

    def test_cant_set_audio_to_int(self):
        with self.assertRaises(ValueError):
            self.commands.set_audio(1)

        self.pipeline_mock.amix.setAudioSource.assert_not_called()
