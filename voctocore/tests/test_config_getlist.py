from voctocore.lib.config import Config
from voctocore.tests.helper.voctomix_test import VoctomixTest


# noinspection PyUnusedLocal
class AudiomixMultipleSources(VoctomixTest):
    def test_empty_string_results_in_empty_list(self):
        Config.given("foo", "bar", "")
        self.assertEqual(Config.getList("foo", "bar"), [])

    def test_string_with_only_spaces_results_in_empty_list(self):
        Config.given("foo", "bar", "  ")
        self.assertEqual(Config.getList("foo", "bar"), [])

    def test_string_surrounded_by_spaces_results_in_stripped_single_item_list(self):
        Config.given("foo", "bar", " moo ")
        self.assertEqual(Config.getList("foo", "bar"), ["moo"])

    def test_empty_items_are_removed_from_list(self):
        Config.given("foo", "bar", "moo,,qoo")
        self.assertEqual(Config.getList("foo", "bar"), ["moo", "qoo"])

    def test_items_surounded_by_spaces_are_trimmed(self):
        Config.given("foo", "bar", " moo ,  qoo,doo ")
        self.assertEqual(Config.getList("foo", "bar"), ["moo", "qoo", "doo"])
