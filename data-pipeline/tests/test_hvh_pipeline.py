import json
import os
import subprocess
import unittest
from pathlib import Path
# suppress NotOpenSSLWarning: urllib3
import warnings
warnings.filterwarnings("ignore", module="urllib3")

from pipeline.sources.museums.hvh.mapper import HvhMapper
from pipeline.sources.museums.hvh.parser import parse_oai_record_xml, parse_list_identifiers_xml


PIPELINE = Path(os.environ.get("PIPELINE_DIR", "/Users/lux/data-pipeline"))
FIXTURES = Path(__file__).parent / "fixtures"
TEST_HVH_ID = os.environ.get("TEST_HVH_ID") or os.environ.get("TEST_PRIREF", "5061-06")
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
        path = PIPELINE / "data" / "output" / "latest" / "export_full_0.jsonl"
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

        path_part = uri.removeprefix("http://localhost:8000/data/")
        try:
            raw = subprocess.check_output(
                ["curl", "-sf", f"http://localhost:8000/data/{path_part}"],
                text=True,
            )
        except Exception as exc:
            _skip_or_fail(self, f"API record endpoint is unavailable: {exc}")

        record = json.loads(raw)
        self.assertEqual(_missing_fields(record, [*LINKED_ART_REQUIRED_FIELDS, "_links"]), [])


if __name__ == "__main__":
    unittest.main()
