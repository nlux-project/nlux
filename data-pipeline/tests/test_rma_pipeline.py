import json
import unittest
from pathlib import Path

from pipeline.sources.museums.rma.fetcher import RmaFetcher
from pipeline.sources.museums.rma.mapper import RmaMapper


FIXTURES = Path(__file__).parent / "fixtures"


def _load_json(path):
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


class DummyIdMap(dict):
    update_token = "__test__"


class DummyConfigs:
    def __init__(self):
        self.data_dir = str(FIXTURES)
        self.allow_network = False
        self.globals = {}
        self.results = {"merged": {}}
        self.external = {}
        self.internal = {}

    def get_idmap(self):
        return DummyIdMap()

    def canonicalize(self, uri):
        return uri


class RmaPipelineIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.record = _load_json(FIXTURES / "rma-record-200107928.json")
        self.mapper = RmaMapper(
            {
                "name": "rma",
                "namespace": "https://id.rijksmuseum.nl/",
                "all_configs": DummyConfigs(),
            }
        )

    def test_fetcher_builds_resolver_request(self):
        fetcher = RmaFetcher(
            {
                "name": "rma",
                "fetch": "",
                "resolverBase": "https://id.rijksmuseum.nl",
                "all_configs": DummyConfigs(),
            }
        )

        self.assertEqual(fetcher.fix_identifier("https://id.rijksmuseum.nl/200107928"), "200107928")
        self.assertTrue(fetcher.validate_identifier("200107928"))
        self.assertEqual(fetcher.make_fetch_uri("200107928"), "https://id.rijksmuseum.nl/200107928")

    def test_mapper_normalizes_linked_art_record(self):
        mapped = self.mapper.transform({"data": self.record})
        self.assertEqual(mapped["identifier"], "200107928")
        self.assertEqual(mapped["source"], "rma")

        data = mapped["data"]
        self.assertEqual(data["id"], "https://id.rijksmuseum.nl/200107928")
        self.assertEqual(data["type"], "HumanMadeObject")
        self.assertEqual(data["_label"], "The Night Watch")
        self.assertEqual(data["current_owner"][0]["_label"], "Rijksmuseum Amsterdam")
        self.assertEqual(data["member_of"][-1]["_label"], "Rijksmuseum Amsterdam")
        self.assertEqual(data["classified_as"][0]["_label"], "painting")
        self.assertEqual(data["equivalent"][0]["id"], "http://hdl.handle.net/10934/RM0001.COLLECT.5216")
        self.assertEqual(data["equivalent"][0]["type"], "HumanMadeObject")


if __name__ == "__main__":
    unittest.main()
