import unittest
from pathlib import Path

from pipeline.sources.museums.hvh.mapper import HvhMapper
from pipeline.sources.museums.hvh.parser import parse_oai_record_xml, parse_list_identifiers_xml


FIXTURES = Path(__file__).parent / "fixtures"


class DummyIdMap(dict):
    update_token = "__test__"


class DummyConfigs:
    def __init__(self):
        self.data_dir = str(FIXTURES)
        self.globals = {}
        self.results = {"merged": {}}
        self.external = {}
        self.internal = {}

    def get_idmap(self):
        return DummyIdMap()

    def canonicalize(self, uri):
        return uri


class HvhPipelineTest(unittest.TestCase):
    def setUp(self):
        xml = (FIXTURES / "hvh-getrecord-5061-06.xml").read_text()
        self.record = parse_oai_record_xml(xml)
        self.mapper = HvhMapper(
            {
                "name": "hvh",
                "namespace": "https://collectie.huisvanhilde.nl/resource/",
                "all_configs": DummyConfigs(),
            }
        )

    def test_parse_oai_record_xml(self):
        self.assertEqual(self.record["dc:identifier"][0]["value"], "5061-06")
        self.assertEqual(self.record["dcterms:temporal"][0]["value"], "850-900")
        self.assertEqual(self.record["dcterms_medium"][0]["value"], "Brons")
        self.assertEqual(len(self.record["europeana_isshownby"]), 2)

    def test_parse_list_identifiers_xml(self):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/">
  <ListIdentifiers>
    <header><dc_identifier>4897-01</dc_identifier></header>
    <header><dc_identifier>4897-02</dc_identifier></header>
    <resumptionToken>next-page-token</resumptionToken>
  </ListIdentifiers>
</OAI-PMH>
"""
        identifiers, token = parse_list_identifiers_xml(xml)
        self.assertEqual(identifiers, ["4897-01", "4897-02"])
        self.assertEqual(token, "next-page-token")

    def test_mapper_transforms_record(self):
        mapped = self.mapper.transform({"data": self.record})
        self.assertEqual(mapped["identifier"], "5061-06")
        data = mapped["data"]

        self.assertEqual(data["type"], "HumanMadeObject")
        self.assertEqual(data["_label"], "Pseudo-muntfibula/bracteatenfibula")
        self.assertIn("identified_by", data)
        self.assertIn("made_of", data)
        self.assertIn("produced_by", data)
        self.assertIn("classified_as", data)
        self.assertIn("current_owner", data)
        self.assertIn("subject_of", data)
        self.assertIn("representation", data)


if __name__ == "__main__":
    unittest.main()
