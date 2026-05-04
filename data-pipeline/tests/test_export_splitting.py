import unittest

from pipeline.process.export_splitting import (
    collection_sources_for_record,
    export_filename,
)


class DummyConfigs:
    internal = {
        "teylers": {
            "name": "teylers",
            "type": "internal",
            "matches": ["teylers.adlibhosting.com/ais6/Details/museum/"],
        },
        "hvh": {
            "name": "hvh",
            "type": "internal",
            "matches": ["collectie.huisvanhilde.nl/resource/"],
        },
    }

    def split_uri(self, uri):
        for source in self.internal.values():
            for match in source["matches"]:
                if match in uri:
                    return source, uri.rsplit(match, 1)[1]
        return None


class ExportSplittingTest(unittest.TestCase):
    def test_export_filename_is_collection_specific(self):
        self.assertEqual(export_filename("teylers", 0), "export_teylers_0.jsonl")

    def test_uses_record_sources_when_available(self):
        sources = collection_sources_for_record(
            {"sources": ["teylers", "aat"]},
            {"equivalent": []},
            DummyConfigs(),
        )
        self.assertEqual(sources, ["teylers"])

    def test_falls_back_to_equivalent_source_uri(self):
        sources = collection_sources_for_record(
            {},
            {
                "equivalent": [
                    {
                        "id": "https://collectie.huisvanhilde.nl/resource/5061-06",
                    }
                ]
            },
            DummyConfigs(),
        )
        self.assertEqual(sources, ["hvh"])

    def test_shared_file_for_unassigned_records(self):
        sources = collection_sources_for_record({}, {"equivalent": []}, DummyConfigs())
        self.assertEqual(sources, ["shared"])


if __name__ == "__main__":
    unittest.main()
