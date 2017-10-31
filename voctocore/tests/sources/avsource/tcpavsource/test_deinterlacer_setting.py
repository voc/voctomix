import io

from mock import MagicMock

from tests.helper.voctomix_test import VoctomixTest
from gi.repository import Gst
from lib.sources import TCPAVSource
from lib.config import Config


# noinspection PyUnusedLocal
class AudiomixMultipleSources(VoctomixTest):
    def setUp(self):
        super().setUp()

        Config.given("mix", "videocaps", "video/x-raw")

        self.source = TCPAVSource('cam1', 42, ['test_mixer', 'test_preview'], has_audio=True, has_video=True)
        self.mock_fp = MagicMock(spec=io.IOBase)

    def test_unconfigured_does_not_add_a_deinterlacer(self):
        pipeline = self.simulate_connection_and_aquire_pipeline_description()
        self.assertRegexAnyWhitespace(pipeline, "demux. ! video/x-raw ! queue ! tee name=vtee")

    def test_no_does_not_add_a_deinterlacer(self):
        Config.given("source.cam1", "deinterlace", "no")

        pipeline = self.simulate_connection_and_aquire_pipeline_description()
        self.assertRegexAnyWhitespace(pipeline, "demux. ! video/x-raw ! queue ! tee name=vtee")

    def test_yes_does_add_yadif(self):
        Config.given("source.cam1", "deinterlace", "yes")

        pipeline = self.simulate_connection_and_aquire_pipeline_description()
        self.assertRegexAnyWhitespace(pipeline, "demux. ! video/x-raw ! yadif mode=interlaced name=deinter")

    def test_assume_progressive_does_add_capssetter(self):
        Config.given("source.cam1", "deinterlace", "assume-progressive")

        pipeline = self.simulate_connection_and_aquire_pipeline_description()
        self.assertRegexAnyWhitespace(
            pipeline,
            "demux. ! video/x-raw ! capssetter caps=video/x-raw,interlace-mode=progressive name=deinter"
        )

    def simulate_connection_and_aquire_pipeline_description(self):
        Gst.parse_launch.reset_mock()
        self.source.on_accepted(self.mock_fp, '127.0.0.42')

        Gst.parse_launch.assert_called()
        args, kwargs = Gst.parse_launch.call_args_list[0]
        pipeline = args[0]

        return pipeline

    def assertRegexAnyWhitespace(self, text, regex):
        regex = regex.replace(" ", "\s*")
        self.assertRegex(text, regex)
