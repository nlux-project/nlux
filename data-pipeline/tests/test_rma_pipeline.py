import json
import os
import subprocess
import unittest
from pathlib import Path
from urllib.parse import quote

# suppress NotOpenSSLWarning: urllib3
import warnings
warnings.filterwarnings("ignore", module="urllib3")

from pipeline.sources.museums.rma.fetcher import RmaFetcher
from pipeline.sources.museums.rma.mapper import RmaMapper


FIXTURES = Path(__file__).parent / "fixtures"
PIPELINE = Path(os.environ.get("PIPELINE_DIR", "/Users/lux/data-pipeline"))
TEST_RMA_ID = os.environ.get("TEST_RMA_ID", "200107928")
RMA_COLLECTION_LABEL = "Rijksmuseum Amsterdam"
REQUIRE_LIVE = os.environ.get("RMA_REQUIRE_LIVE") == "1"

RAW_REQUIRED_FIELDS = [
    "id",
    "type",
    "identified_by",
]

LINKED_ART_REQUIRED_FIELDS = [
    "identified_by",
    "classified_as",
    "member_of",
    "current_owner",
    "equivalent",
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


def _identified_by_content(record):
    return [
        identifier.get("content")
        for identifier in record.get("identified_by", []) or []
        if isinstance(identifier, dict) and identifier.get("content")
    ]


def _member_labels(record):
    member_of = record.get("member_of") or []
    if isinstance(member_of, dict):
        member_of = [member_of]
    return [member.get("_label") for member in member_of if isinstance(member, dict)]


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

    def _api_record_uri(self):
        source_uri = f"id.rijksmuseum.nl/{TEST_RMA_ID}"
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
            raw = subprocess.check_output(["curl", "-sf", url], text=True)
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
        self.assertEqual(_missing_fields(data, LINKED_ART_REQUIRED_FIELDS), [])
        self.assertEqual(data["current_owner"][0]["_label"], RMA_COLLECTION_LABEL)
        self.assertEqual(data["member_of"][-1]["_label"], RMA_COLLECTION_LABEL)
        self.assertEqual(data["classified_as"][0]["_label"], "painting")
        self.assertEqual(data["equivalent"][0]["id"], "http://hdl.handle.net/10934/RM0001.COLLECT.5216")
        self.assertEqual(data["equivalent"][0]["type"], "HumanMadeObject")
        self.assertIn("SK-C-5", _identified_by_content(data))
        self.assertNotIn(
            '"id": "https://id.rijksmuseum.nl/301234479"',
            json.dumps(data, ensure_ascii=False),
            "unsupported BIBFRAME references should not be queued for reconciliation",
        )
        self.assertNotIn(
            '"id": "https://id.rijksmuseum.nl/301234480"',
            json.dumps(data, ensure_ascii=False),
            "list-valued types should not be queued for reconciliation",
        )

    def test_harvest_file(self):
        path = PIPELINE / "data" / "input" / "rma" / f"{TEST_RMA_ID}.json"
        if not path.exists():
            _skip_or_fail(self, f"Harvest file not found: {path}")

        record = _load_json(path)
        self.assertEqual(_missing_fields(record, RAW_REQUIRED_FIELDS), [])
        self.assertEqual(str(record.get("id", "")).rstrip("/").rsplit("/", 1)[-1], TEST_RMA_ID)

    def test_datacache_record(self):
        try:
            with _connect_pg(self) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT data FROM rma_data_cache WHERE data->>'id' LIKE %s", (f"%/{TEST_RMA_ID}",))
                    row = cur.fetchone()
        except Exception as exc:
            _skip_or_fail(self, f"RMA datacache table is unavailable: {exc}")

        if not row:
            _skip_or_fail(self, "Record not found in rma_data_cache")

        record = _coerce_record(row[0])
        self.assertEqual(_missing_fields(record, RAW_REQUIRED_FIELDS), [])

    def test_reconciled_record(self):
        try:
            with _connect_pg(self) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT data FROM rma_record_cache WHERE identifier = %s", (TEST_RMA_ID,))
                    row = cur.fetchone()
        except Exception as exc:
            _skip_or_fail(self, f"RMA record cache table is unavailable: {exc}")

        if not row:
            _skip_or_fail(self, "Record not found in rma_record_cache")

        record = _coerce_record(row[0])
        self.assertEqual(_missing_fields(record, LINKED_ART_REQUIRED_FIELDS), [])
        self.assertIn(RMA_COLLECTION_LABEL, _member_labels(record))

    def test_rewritten_record(self):
        try:
            with _connect_pg(self) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT data FROM rma_rewritten_record_cache "
                        "WHERE data::text LIKE %s LIMIT 1",
                        (f"%{TEST_RMA_ID}%",),
                    )
                    row = cur.fetchone()
        except Exception as exc:
            _skip_or_fail(self, f"RMA rewritten record cache table is unavailable: {exc}")

        if not row:
            _skip_or_fail(self, "Record not found in rma_rewritten_record_cache")

        record = _coerce_record(row[0])
        self.assertEqual(_missing_fields(record, LINKED_ART_REQUIRED_FIELDS), [])

    def test_export_record(self):
        path = PIPELINE / "data" / "output" / "latest" / "export_rma_0.jsonl"
        if not path.exists():
            _skip_or_fail(self, f"Export file not found: {path}")

        with path.open(encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                record = _coerce_record(json.loads(line))
                equivalents = record.get("equivalent", [])
                candidate_text = json.dumps(
                    {
                        "id": record.get("id"),
                        "equivalent": equivalents,
                        "identified_by": record.get("identified_by"),
                    },
                    ensure_ascii=False,
                )
                if TEST_RMA_ID in candidate_text or "SK-C-5" in candidate_text:
                    self.assertEqual(_missing_fields(record, LINKED_ART_REQUIRED_FIELDS), [])
                    self.assertTrue(record["member_of"][0].get("id"), "member_of should have a resolvable id")
                    self.assertTrue(record["current_owner"][0].get("id"), "current_owner should have a resolvable id")
                    self.assertIn(RMA_COLLECTION_LABEL, _member_labels(record))
                    return

        _skip_or_fail(self, "Record not found in export")

    def test_api_record(self):
        if not REQUIRE_LIVE:
            self.skipTest("live API test")

        record = self._api_get_data(self._api_record_uri())
        self.assertEqual(record["type"], "HumanMadeObject")
        self.assertIn(RMA_COLLECTION_LABEL, _member_labels(record))
        self.assertTrue(record["member_of"][0].get("id"), "member_of should have a resolvable id")
        self.assertTrue(record["current_owner"][0].get("id"), "current_owner should have a resolvable id")
        self.assertTrue(
            "SK-C-5" in json.dumps(record.get("identified_by", []), ensure_ascii=False)
            or "The Night Watch" in json.dumps(record, ensure_ascii=False)
            or "De Nachtwacht" in json.dumps(record, ensure_ascii=False)
        )

    def test_api_search_finds_night_watch(self):
        if not REQUIRE_LIVE:
            self.skipTest("live API test")

        results = self._api_search("item", "Nachtwacht")
        records = [
            self._api_get_data(item["id"])
            for item in results.get("orderedItems", [])
            if item.get("type") == "HumanMadeObject" and item.get("id")
        ]

        self.assertTrue(records, "item search should return records for Nachtwacht")
        self.assertTrue(
            any("SK-C-5" in json.dumps(record, ensure_ascii=False) for record in records),
            "Nachtwacht search should include Rijksmuseum object SK-C-5",
        )

    def test_api_rma_collection_record(self):
        if not REQUIRE_LIVE:
            self.skipTest("live API test")

        results = self._api_search("set", RMA_COLLECTION_LABEL)
        sets = [
            self._api_get_data(item["id"])
            for item in results.get("orderedItems", [])
            if item.get("type") == "Set" and item.get("id")
        ]

        self.assertTrue(sets, "set search should return the Rijksmuseum Amsterdam collection")
        self.assertTrue(
            any(record.get("_label") == RMA_COLLECTION_LABEL for record in sets),
            "Rijksmuseum Amsterdam collection should have a matching Set label",
        )


if __name__ == "__main__":
    unittest.main()
