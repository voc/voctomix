from tests.helper.voctomix_test import VoctomixTest
from gi.repository import Gst
from lib.sources import DeckLinkAVSource
from lib.config import Config


# noinspection PyUnusedLocal
class AudiomixMultipleSources(VoctomixTest):
    def setUp(self):
        super().setUp()

        Config.given("mix", "videocaps", "video/x-raw")
        Config.given("source.cam1", "kind", "decklink")
        Config.given("source.cam1", "devicenumber", "23")

        self.source = DeckLinkAVSource('cam1', ['test_mixer', 'test_preview'], has_audio=True, has_video=True)

    def test_unconfigured_does_not_add_a_deinterlacer(self):
        pipeline = self.simulate_connection_and_aquire_pipeline_description()
        self.assertRegexAnyWhitespace(pipeline, "videoconvert ! videoscale")

    def test_no_does_not_add_a_deinterlacer(self):
        Config.given("source.cam1", "deinterlace", "no")

        pipeline = self.simulate_connection_and_aquire_pipeline_description()
        self.assertRegexAnyWhitespace(pipeline, "videoconvert ! videoscale")

    def test_yes_does_add_yadif(self):
        Config.given("source.cam1", "deinterlace", "yes")

        pipeline = self.simulate_connection_and_aquire_pipeline_description()
        self.assertRegexAnyWhitespace(pipeline, "mode=1080i50 ! yadif mode=interlaced ! videoconvert")

    def test_assume_progressive_does_add_capssetter(self):
        Config.given("source.cam1", "deinterlace", "assume-progressive")

        pipeline = self.simulate_connection_and_aquire_pipeline_description()
        self.assertRegexAnyWhitespace(
            pipeline,
            "mode=1080i50 ! capssetter caps=video/x-raw,interlace-mode=progressive ! videoconvert"
        )

    def simulate_connection_and_aquire_pipeline_description(self):
        Gst.parse_launch.reset_mock()
        self.source.launch_pipeline()

        Gst.parse_launch.assert_called()
        args, kwargs = Gst.parse_launch.call_args_list[0]
        pipeline = args[0]

        return pipeline

    def assertRegexAnyWhitespace(self, text, regex):
        regex = regex.replace(" ", "\s*")
        self.assertRegex(text, regex)
