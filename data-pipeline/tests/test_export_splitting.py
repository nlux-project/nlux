import unittest

from pipeline.process.export_splitting import (
    collection_sources_for_record,
    export_filename,
    filter_collection_sources,
    pop_source_filters,
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
        "wfm": {
            "name": "wfm",
            "type": "internal",
            "matches": ["westfriesmuseum.com/detail/"],
        },
        "nha-c587": {
            "name": "nha-c587",
            "type": "internal",
            "matches": ["hdl.handle.net/21.12102/"],
        },
        "nha-c480": {
            "name": "nha-c480",
            "type": "internal",
            "matches": ["hdl.handle.net/21.12102/"],
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

    def test_falls_back_to_wfm_equivalent_source_uri(self):
        sources = collection_sources_for_record(
            {},
            {
                "equivalent": [
                    {
                        "id": "https://westfriesmuseum.com/detail/c396d24a-de49-11e6-836d-d89d6717b464",
                    }
                ]
            },
            DummyConfigs(),
        )
        self.assertEqual(sources, ["wfm"])

    def test_falls_back_to_nha_c587_equivalent_source_uri(self):
        sources = collection_sources_for_record(
            {},
            {
                "equivalent": [
                    {
                        "id": "https://hdl.handle.net/21.12102/F7DDF7EEFB8E11DF9E4D523BC2E286E2",
                    }
                ]
            },
            DummyConfigs(),
        )
        self.assertEqual(sources, ["nha-c587"])

    def test_uses_record_source_for_nha_c480(self):
        sources = collection_sources_for_record(
            {"source": "nha-c480"},
            {
                "equivalent": [
                    {
                        "id": "https://hdl.handle.net/21.12102/65B76D9AFB8F11DF9E4D523BC2E286E2",
                    }
                ]
            },
            DummyConfigs(),
        )
        self.assertEqual(sources, ["nha-c480"])

    def test_shared_file_for_unassigned_records(self):
        sources = collection_sources_for_record({}, {"equivalent": []}, DummyConfigs())
        self.assertEqual(sources, ["shared"])

    def test_pop_source_filters_consumes_known_source_flags(self):
        argv = ["run-export.py", "0", "1", "--wfm", "--nha-c587", "--nha-c480", "--export-entities"]

        selected = pop_source_filters(argv, ["teylers", "hvh", "wfm", "nha-c587", "nha-c480"])

        self.assertEqual(selected, {"wfm", "nha-c587", "nha-c480"})
        self.assertEqual(argv, ["run-export.py", "0", "1", "--export-entities"])

    def test_filter_collection_sources_keeps_selected_sources(self):
        self.assertEqual(
            filter_collection_sources(["teylers", "wfm"], {"wfm"}),
            ["wfm"],
        )
        self.assertEqual(filter_collection_sources(["wfm"], set()), ["wfm"])


if __name__ == "__main__":
    unittest.main()
