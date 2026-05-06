import json
import os
import subprocess
import unittest
from pathlib import Path
from urllib.parse import quote
# suppress NotOpenSSLWarning: urllib3
import warnings
warnings.filterwarnings("ignore", module="urllib3")

from pipeline.sources.museums.hvh.mapper import HvhMapper
from pipeline.sources.museums.hvh.parser import parse_oai_record_xml, parse_list_identifiers_xml


PIPELINE = Path(os.environ.get("PIPELINE_DIR", "/Users/lux/data-pipeline"))
FIXTURES = Path(__file__).parent / "fixtures"
TEST_HVH_ID = os.environ.get("TEST_HVH_ID") or os.environ.get("TEST_PRIREF", "5061-06")
HVH_COLLECTION_URI = "http://localhost:8000/data/set/5938ba10-2285-5b40-b5c4-ab17473021c3"
HVH_OWNER_URI = "http://localhost:8000/data/group/e31c637a-00b2-541d-94f3-1730925ae40a"
REQUIRE_LIVE = os.environ.get("HVH_REQUIRE_LIVE") == "1"

RAW_REQUIRED_FIELDS = [
    "dc:identifier",
    "dc:title",
    "dc:description",
    "dcterms:temporal",
    "dcterms_medium",
    "deeplinkpubl",
]

LINKED_ART_REQUIRED_FIELDS = [
    "identified_by",
    "classified_as",
    "member_of",
    "current_owner",
    "subject_of",
]


def _skip_or_fail(testcase, message):
    if REQUIRE_LIVE:
        testcase.fail(message)
    testcase.skipTest(message)


def _coerce_record(value):
    if isinstance(value, str):
        value = json.loads(value)
    if isinstance(value, dict) and "data" in value:
        return value["data"]
    return value


def _load_json(path):
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def _missing_fields(record, fields):
    return [field for field in fields if field not in record]


def _has_classification(record, label=None, equivalent_id=None):
    for classification in record.get("classified_as", []) or []:
        if label and classification.get("_label") == label:
            return True
        if equivalent_id and any(
            equivalent.get("id") == equivalent_id
            for equivalent in classification.get("equivalent", []) or []
        ):
            return True
    return False


def _identified_by_content(record):
    return [
        identifier.get("content")
        for identifier in record.get("identified_by", []) or []
        if identifier.get("content")
    ]


def _connect_pg(testcase):
    try:
        import psycopg2
    except ImportError:
        _skip_or_fail(testcase, "psycopg2 is not installed")

    try:
        return psycopg2.connect(host="localhost", user="postgres", password="admin123", dbname="postgres")
    except Exception as exc:
        _skip_or_fail(testcase, f"PostgreSQL is unavailable: {exc}")


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


class HvhPipelineIntegrationTest(unittest.TestCase):
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

    def _api_record_uri(self):
        source_uri = f"collectie.huisvanhilde.nl/resource/{TEST_HVH_ID}"
        try:
            uri = subprocess.check_output(
                [
                    "docker",
                    "exec",
                    "nlux-api-1",
                    "python3",
                    "-c",
                    (
                        "import sqlite3\n"
                        "conn = sqlite3.connect('/data/nlux.db')\n"
                        "cur = conn.cursor()\n"
                        "cur.execute(\"SELECT uri FROM records WHERE data LIKE ? LIMIT 1\", "
                        f"('%{source_uri}%',))\n"
                        "row = cur.fetchone()\n"
                        "print(row[0] if row else '')\n"
                        "conn.close()\n"
                    ),
                ],
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
        except Exception as exc:
            _skip_or_fail(self, f"Docker API database is unavailable: {exc}")

        if not uri:
            _skip_or_fail(self, "Record not found in API database")
        return uri

    def _api_get_json(self, url):
        try:
            raw = subprocess.check_output(
                [
                    "docker",
                    "exec",
                    "-i",
                    "nlux-api-1",
                    "python3",
                    "-c",
                    (
                        "import sys, urllib.request\n"
                        "url = sys.stdin.read().strip().replace('http://localhost:8000', 'http://127.0.0.1:8000')\n"
                        "print(urllib.request.urlopen(url, timeout=10).read().decode())\n"
                    ),
                ],
                input=url,
                text=True,
                stderr=subprocess.DEVNULL,
            )
        except Exception as exc:
            _skip_or_fail(self, f"API endpoint is unavailable: {exc}")
        return json.loads(raw)

    def _api_get_data(self, uri):
        path_part = uri.removeprefix("http://localhost:8000/data/")
        return self._api_get_json(f"http://localhost:8000/data/{path_part}")

    def _api_search(self, scope, query):
        return self._api_get_json(
            f"http://localhost:8000/api/search/{scope}?q={quote(query)}&page=1&pageLength=10"
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
        self.assertIn("member_of", data)
        self.assertIn("current_owner", data)
        self.assertIn("current_location", data)
        self.assertIn("encountered_by", data)
        self.assertIn("subject_of", data)
        self.assertIn("representation", data)
        self.assertEqual(data["member_of"][0]["_label"], "Huis van Hilde")

        self.assertEqual(data["current_location"]["_label"], "Depot C")
        encounter = data["encountered_by"][0]
        self.assertEqual(encounter["took_place_at"][0]["_label"], "De Krocht, Limmen, Castricum, Kennemerland")
        self.assertEqual(encounter["carried_out_by"][0]["_label"], "Diachron UvA bv")
        self.assertTrue(
            any(note.get("content") == "-/0.4/2.3" for note in data.get("referred_to_by", []))
        )

    def test_harvest_file(self):
        path = PIPELINE / "data" / "input" / "hvh" / f"{TEST_HVH_ID}.json"
        if not path.exists():
            _skip_or_fail(self, f"Harvest file not found: {path}")

        record = _load_json(path)
        self.assertEqual(_missing_fields(record, RAW_REQUIRED_FIELDS), [])
        values = record.get("dc:identifier", [])
        self.assertTrue(any(value.get("value") == TEST_HVH_ID for value in values))

    def test_datacache_record(self):
        with _connect_pg(self) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT data FROM hvh_data_cache WHERE identifier = %s", (TEST_HVH_ID,))
                row = cur.fetchone()

        if not row:
            _skip_or_fail(self, "Record not found in hvh_data_cache")

        record = _coerce_record(row[0])
        values = record.get("dc:identifier", [])
        self.assertTrue(any(value.get("value") == TEST_HVH_ID for value in values))

    def test_reconciled_record(self):
        with _connect_pg(self) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT data FROM hvh_record_cache WHERE identifier = %s", (TEST_HVH_ID,))
                row = cur.fetchone()

        if not row:
            _skip_or_fail(self, "Record not found in hvh_record_cache")

        record = _coerce_record(row[0])
        self.assertEqual(_missing_fields(record, LINKED_ART_REQUIRED_FIELDS), [])

    def test_rewritten_record(self):
        with _connect_pg(self) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT data FROM hvh_rewritten_record_cache "
                    "WHERE data::text LIKE %s LIMIT 1",
                    (f"%{TEST_HVH_ID}%",),
                )
                row = cur.fetchone()

        if not row:
            _skip_or_fail(self, "Record not found in hvh_rewritten_record_cache")

        record = _coerce_record(row[0])
        self.assertEqual(_missing_fields(record, LINKED_ART_REQUIRED_FIELDS), [])

    def test_export_record(self):
        path = PIPELINE / "data" / "output" / "latest" / "export_hvh_0.jsonl"
        if not path.exists():
            _skip_or_fail(self, f"Export file not found: {path}")

        source_uri = f"collectie.huisvanhilde.nl/resource/{TEST_HVH_ID}"
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                record = _coerce_record(json.loads(line))
                equivalents = record.get("equivalent", [])
                if any(source_uri in eq.get("id", "") for eq in equivalents):
                    self.assertEqual(_missing_fields(record, LINKED_ART_REQUIRED_FIELDS), [])
                    return

        _skip_or_fail(self, "Record not found in export")

    def test_api_record(self):
        record = self._api_get_data(self._api_record_uri())
        self.assertEqual(_missing_fields(record, [*LINKED_ART_REQUIRED_FIELDS, "_links"]), [])

    def test_api_record_has_resolvable_collection_and_owner(self):
        record = self._api_get_data(self._api_record_uri())
        collection_uri = record["member_of"][0].get("id")
        owner_uri = record["current_owner"][0].get("id")

        self.assertTrue(collection_uri, "member_of should have a resolvable id")
        self.assertTrue(owner_uri, "current_owner should have a resolvable id")

        collection = self._api_get_data(collection_uri)
        self.assertEqual(collection["type"], "Set")
        self.assertEqual(collection["_label"], "Huis van Hilde")

        owner = self._api_get_data(owner_uri)
        self.assertEqual(owner["type"], "Group")
        self.assertEqual(owner["_label"], "Provinciaal Depot voor Archeologie Noord-Holland")

    def test_api_search_finds_collection_and_owner(self):
        set_results = self._api_search("set", "Huis van Hilde")
        self.assertTrue(
            any(
                item.get("type") == "Set"
                and self._api_get_data(item["id"]).get("_label") == "Huis van Hilde"
                for item in set_results.get("orderedItems", [])
            ),
            "set search should return the Huis van Hilde collection",
        )

        agent_results = self._api_search("agent", "Provinciaal Depot voor Archeologie Noord-Holland")
        self.assertTrue(
            any(
                item.get("type") == "Group"
                and self._api_get_data(item["id"]).get("_label") == "Provinciaal Depot voor Archeologie Noord-Holland"
                for item in agent_results.get("orderedItems", [])
            ),
            "agent search should return the Huis van Hilde owner group",
        )

    def test_api_hvh_collection_record(self):
        record = self._api_get_data(HVH_COLLECTION_URI)

        self.assertEqual(record["id"], HVH_COLLECTION_URI)
        self.assertEqual(record["type"], "Set")
        self.assertEqual(record["_label"], "Huis van Hilde")
        self.assertIn("Huis van Hilde", _identified_by_content(record))
        self.assertTrue(
            _has_classification(
                record,
                label="Named Collection",
                equivalent_id="http://vocab.getty.edu/aat/300456764",
            ),
            "collection should be classified as a named collection",
        )

    def test_api_hvh_owner_group_record(self):
        record = self._api_get_data(HVH_OWNER_URI)

        self.assertEqual(record["id"], HVH_OWNER_URI)
        self.assertEqual(record["type"], "Group")
        self.assertEqual(record["_label"], "Provinciaal Depot voor Archeologie Noord-Holland")
        self.assertIn("Provinciaal Depot voor Archeologie Noord-Holland", _identified_by_content(record))


if __name__ == "__main__":
    unittest.main()
