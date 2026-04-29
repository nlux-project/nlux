import json
import os
import subprocess
import unittest
from pathlib import Path

import warnings
warnings.filterwarnings("ignore", module="urllib3")

from pipeline.sources.museums.rbhc.fetcher import RbhcFetcher
from pipeline.sources.museums.rbhc.mapper import RbhcMapper


PIPELINE = Path(os.environ.get("PIPELINE_DIR", "/Users/lux/data-pipeline"))
FIXTURES = Path(__file__).parent / "fixtures"
TEST_PRIREF = os.environ.get("TEST_PRIREF", "2")
REQUIRE_LIVE = os.environ.get("RBHC_REQUIRE_LIVE") == "1"

RAW_REQUIRED_FIELDS = [
    "@priref",
    "@created",
    "@modification",
    "Title",
    "Object_name",
    "Production",
    "Production_date",
    "Reproduction",
    "object_number",
]

LINKED_ART_REQUIRED_FIELDS = [
    "identified_by",
    "classified_as",
    "produced_by",
    "dimension",
    "member_of",
    "current_owner",
    "subject_of",
    "representation",
]


def _skip_or_fail(testcase, message):
    if REQUIRE_LIVE:
        testcase.fail(message)
    testcase.skipTest(message)


def _load_json(path):
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def _coerce_record(value):
    if isinstance(value, str):
        value = json.loads(value)
    if isinstance(value, dict) and "data" in value:
        return value["data"]
    return value


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
        self.allow_network = False
        self.globals = {}
        self.results = {"merged": {}}
        self.external = {}
        self.internal = {}

    def get_idmap(self):
        return DummyIdMap()

    def canonicalize(self, uri):
        return uri


class RbhcPipelineIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.record = _load_json(FIXTURES / "rbhc-record-2.json")
        self.mapper = RbhcMapper(
            {
                "name": "rbhc",
                "namespace": "https://mmb-web.adlibhosting.com/ais6/Details/collect/",
                "all_configs": DummyConfigs(),
            }
        )

    def test_fetcher_builds_collect_webapi_uri(self):
        fetcher = RbhcFetcher({"name": "rbhc", "fetch": "", "all_configs": DummyConfigs()})
        self.assertTrue(fetcher.validate_identifier("2"))
        self.assertFalse(fetcher.validate_identifier("V23890"))
        uri = fetcher.make_fetch_uri("2")
        self.assertIn("database=collect", uri)
        self.assertIn("search=priref+%3D+2", uri)
        self.assertIn("reproduction.reference", uri)

    def test_fixture_has_required_raw_fields(self):
        self.assertEqual(_missing_fields(self.record, RAW_REQUIRED_FIELDS), [])

    def test_mapper_transforms_record(self):
        mapped = self.mapper.transform({"data": self.record})
        self.assertEqual(mapped["identifier"], "2")
        self.assertEqual(mapped["source"], "rbhc")

        data = mapped["data"]
        self.assertEqual(data["type"], "HumanMadeObject")
        self.assertEqual(data["_label"], "Standaard metre, Etienne Lenoir Parijs, 1795")
        self.assertEqual(_missing_fields(data, LINKED_ART_REQUIRED_FIELDS), [])
        self.assertEqual(data["member_of"][0]["_label"], "Rijksmuseum Boerhaave collection")
        self.assertEqual(data["current_owner"][0]["id"], "http://www.wikidata.org/entity/Q759169")
        self.assertEqual(data["current_location"]["_label"], "HM09V01")
        self.assertEqual(data["produced_by"]["carried_out_by"][0]["_label"], "Lenoir, Etienne")
        self.assertIn("mmb-web.adlibhosting.com/ais6/Details/collect/2", data["subject_of"][0]["digitally_carried_by"][0]["access_point"][0]["id"])
        self.assertIn("Website%5CVoorwerpen", data["representation"][0]["digitally_shown_by"][0]["id"].replace("\\", "%5C"))

    def test_harvest_file(self):
        path = PIPELINE / "data" / "input" / "rbhc" / f"{TEST_PRIREF}.json"
        if not path.exists():
            _skip_or_fail(self, f"Harvest file not found: {path}")

        record = _load_json(path)
        self.assertEqual(_missing_fields(record, RAW_REQUIRED_FIELDS), [])
        self.assertEqual(str(record.get("@priref")), TEST_PRIREF)

    def test_datacache_record(self):
        try:
            with _connect_pg(self) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT data FROM rbhc_data_cache WHERE data->>'@priref' = %s", (TEST_PRIREF,))
                    row = cur.fetchone()
        except Exception as exc:
            _skip_or_fail(self, f"RBHC datacache table is unavailable: {exc}")

        if not row:
            _skip_or_fail(self, "Record not found in rbhc_data_cache")

        record = _coerce_record(row[0])
        self.assertEqual(_missing_fields(record, RAW_REQUIRED_FIELDS), [])

    def test_reconciled_record(self):
        try:
            with _connect_pg(self) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT data FROM rbhc_record_cache WHERE identifier = %s", (TEST_PRIREF,))
                    row = cur.fetchone()
        except Exception as exc:
            _skip_or_fail(self, f"RBHC record cache table is unavailable: {exc}")

        if not row:
            _skip_or_fail(self, "Record not found in rbhc_record_cache")

        record = _coerce_record(row[0])
        self.assertEqual(_missing_fields(record, LINKED_ART_REQUIRED_FIELDS), [])

    def test_rewritten_record(self):
        try:
            with _connect_pg(self) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT data FROM rbhc_rewritten_record_cache "
                        "WHERE data::text LIKE %s LIMIT 1",
                        (f"%collect/{TEST_PRIREF}%",),
                    )
                    row = cur.fetchone()
        except Exception as exc:
            _skip_or_fail(self, f"RBHC rewritten record cache table is unavailable: {exc}")

        if not row:
            _skip_or_fail(self, "Record not found in rbhc_rewritten_record_cache")

        record = _coerce_record(row[0])
        self.assertEqual(_missing_fields(record, LINKED_ART_REQUIRED_FIELDS), [])

    def test_export_record(self):
        path = PIPELINE / "data" / "output" / "latest" / "export_full_0.jsonl"
        if not path.exists():
            _skip_or_fail(self, f"Export file not found: {path}")

        source_uri = f"mmb-web.adlibhosting.com/ais6/Details/collect/{TEST_PRIREF}"
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
        source_uri = f"mmb-web.adlibhosting.com/ais6/Details/collect/{TEST_PRIREF}"
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
            raw = subprocess.check_output(["curl", "-sf", f"http://localhost:8000/data/{path_part}"], text=True)
        except Exception as exc:
            _skip_or_fail(self, f"API record endpoint is unavailable: {exc}")

        record = json.loads(raw)
        self.assertEqual(_missing_fields(record, [*LINKED_ART_REQUIRED_FIELDS, "_links"]), [])


if __name__ == "__main__":
    unittest.main()
