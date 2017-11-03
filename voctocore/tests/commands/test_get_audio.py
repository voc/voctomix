import json

from mock import ANY

from lib.response import OkResponse
from tests.commands.commands_test_base import CommandsTestBase


class GetAudioTest(CommandsTestBase):
    def test_get_audio(self):
        self.pipeline_mock.amix.getAudioVolumes.return_value = [1.0, 0.0, 0.25]

        response = self.commands.get_audio()

        self.assertIsInstance(response, OkResponse)
        self.assertEqual(response.args, ('audio_status', ANY))
        self.assertEqual(json.loads(response.args[1]), {
            "cam1": 1.0,
            "cam2": 0.0,
            "grabber": 0.25
        })
