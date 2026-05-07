import unittest

from pipeline.storage.cache.postgres import _cache_table_name


class PostgresCacheNamingTest(unittest.TestCase):
    def test_cache_table_name_preserves_existing_simple_names(self):
        self.assertEqual(_cache_table_name("wfm", "data_cache"), "wfm_data_cache")

    def test_cache_table_name_sanitizes_hyphenated_source_names(self):
        self.assertEqual(_cache_table_name("nha-c587", "record_cache"), "nha_c587_record_cache")
        self.assertEqual(_cache_table_name("nha-c480", "record_cache"), "nha_c480_record_cache")


if __name__ == "__main__":
    unittest.main()
