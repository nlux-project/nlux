import json
import os
import subprocess
import unittest
from pathlib import Path
from urllib.parse import quote

import warnings
warnings.filterwarnings("ignore", module="urllib3")

from pipeline.sources.museums.wfm.fetcher import WfmFetcher
from pipeline.sources.museums.wfm.mapper import WfmMapper


PIPELINE = Path(os.environ.get("PIPELINE_DIR", "/Users/lux/data-pipeline"))
FIXTURES = Path(__file__).parent / "fixtures"
TEST_WFM_ID = os.environ.get("TEST_WFM_ID") or os.environ.get("TEST_PRIREF", "c396d24a-de49-11e6-836d-d89d6717b464")
REQUIRE_LIVE = os.environ.get("WFM_REQUIRE_LIVE") == "1"

RAW_REQUIRED_FIELDS = [
    "id",
    "title",
    "asset",
    "metadata",
]

LINKED_ART_REQUIRED_FIELDS = [
    "identified_by",
    "classified_as",
    "produced_by",
    "member_of",
    "current_owner",
    "current_location",
    "referred_to_by",
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


class WfmPipelineIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.record = _load_json(FIXTURES / "wfm-record-c396d24a.json")
        self.mapper = WfmMapper(
            {
                "name": "wfm",
                "namespace": "https://westfriesmuseum.com/detail/",
                "all_configs": DummyConfigs(),
            }
        )

    def _api_record_uri(self):
        source_uri = f"westfriesmuseum.com/detail/{TEST_WFM_ID}"
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

    def test_fetcher_builds_memorix_requests(self):
        fetcher = WfmFetcher(
            {
                "name": "wfm",
                "fetch": "",
                "apiUrl": "https://webservices.memorix.nl/mediabank",
                "apiKey": "test-key",
                "all_configs": DummyConfigs(),
            }
        )

        self.assertTrue(fetcher.validate_identifier(TEST_WFM_ID))
        self.assertEqual(
            fetcher.make_fetch_uri(TEST_WFM_ID),
            f"https://webservices.memorix.nl/mediabank/media/{TEST_WFM_ID}",
        )

    def test_fixture_has_required_raw_fields(self):
        self.assertEqual(_missing_fields(self.record, RAW_REQUIRED_FIELDS), [])

    def test_mapper_transforms_record(self):
        mapped = self.mapper.transform({"data": self.record})
        self.assertEqual(mapped["identifier"], TEST_WFM_ID)
        self.assertEqual(mapped["source"], "wfm")

        data = mapped["data"]
        self.assertEqual(data["type"], "HumanMadeObject")
        self.assertEqual(data["_label"], "op papier geplakt, met lijstje in bruine inkt")
        self.assertEqual(_missing_fields(data, LINKED_ART_REQUIRED_FIELDS), [])
        self.assertEqual(data["member_of"][0]["_label"], "Westfries Museum collection")
        self.assertEqual(data["current_owner"][0]["type"], "Group")
        self.assertEqual(data["current_owner"][0]["_label"], "Westfries Museum")
        self.assertNotIn("id", data["current_owner"][0])
        self.assertEqual(data["current_location"]["type"], "Place")
        self.assertEqual(data["current_location"]["_label"], "Westfries Museum")
        self.assertNotIn("id", data["current_location"])
        self.assertEqual(data["produced_by"]["carried_out_by"][0]["_label"], "Cornelis Pronk")
        self.assertEqual(data["produced_by"]["took_place_at"][0]["_label"], "Nederland")
        self.assertIn("1726-01-01T00:00:00", json.dumps(data["produced_by"], ensure_ascii=False))
        self.assertIn("Grootebroek", json.dumps(data["referred_to_by"], ensure_ascii=False))
        self.assertIn(
            "westfriesmuseum.com/detail/c396d24a-de49-11e6-836d-d89d6717b464",
            data["subject_of"][0]["digitally_carried_by"][0]["access_point"][0]["id"],
        )
        image = data["representation"][0]["digitally_shown_by"][0]
        self.assertEqual(image["format"], "image/jpeg")
        self.assertIn("images.memorix.nl", image["access_point"][0]["id"])
        self.assertIn(
            "localhost:8000/iiif/manifest/",
            json.dumps(data["subject_of"], ensure_ascii=False),
        )

    def test_harvest_file(self):
        path = PIPELINE / "data" / "input" / "wfm" / f"{TEST_WFM_ID}.json"
        if not path.exists():
            _skip_or_fail(self, f"Harvest file not found: {path}")

        record = _load_json(path)
        self.assertEqual(_missing_fields(record, RAW_REQUIRED_FIELDS), [])
        self.assertEqual(str(record.get("id")), TEST_WFM_ID)

    def test_datacache_record(self):
        try:
            with _connect_pg(self) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT data FROM wfm_data_cache WHERE data->>'id' = %s", (TEST_WFM_ID,))
                    row = cur.fetchone()
        except Exception as exc:
            _skip_or_fail(self, f"WFM datacache table is unavailable: {exc}")

        if not row:
            _skip_or_fail(self, "Record not found in wfm_data_cache")

        record = _coerce_record(row[0])
        self.assertEqual(_missing_fields(record, RAW_REQUIRED_FIELDS), [])

    def test_reconciled_record(self):
        try:
            with _connect_pg(self) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT data FROM wfm_record_cache WHERE identifier = %s", (TEST_WFM_ID,))
                    row = cur.fetchone()
        except Exception as exc:
            _skip_or_fail(self, f"WFM record cache table is unavailable: {exc}")

        if not row:
            _skip_or_fail(self, "Record not found in wfm_record_cache")

        record = _coerce_record(row[0])
        self.assertEqual(_missing_fields(record, LINKED_ART_REQUIRED_FIELDS), [])

    def test_rewritten_record(self):
        try:
            with _connect_pg(self) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT data FROM wfm_rewritten_record_cache "
                        "WHERE data::text LIKE %s LIMIT 1",
                        (f"%{TEST_WFM_ID}%",),
                    )
                    row = cur.fetchone()
        except Exception as exc:
            _skip_or_fail(self, f"WFM rewritten record cache table is unavailable: {exc}")

        if not row:
            _skip_or_fail(self, "Record not found in wfm_rewritten_record_cache")

        record = _coerce_record(row[0])
        self.assertEqual(_missing_fields(record, LINKED_ART_REQUIRED_FIELDS), [])

    def test_export_record(self):
        path = PIPELINE / "data" / "output" / "latest" / "export_wfm_0.jsonl"
        if not path.exists():
            _skip_or_fail(self, f"Export file not found: {path}")

        source_uri = f"westfriesmuseum.com/detail/{TEST_WFM_ID}"
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                record = _coerce_record(json.loads(line))
                equivalents = record.get("equivalent", [])
                if any(source_uri in eq.get("id", "") for eq in equivalents):
                    self.assertEqual(_missing_fields(record, LINKED_ART_REQUIRED_FIELDS), [])
                    self.assertTrue(record["member_of"][0].get("id"), "member_of should have a resolvable id")
                    self.assertTrue(record["current_owner"][0].get("id"), "current_owner should have a resolvable id")
                    image = record["representation"][0]["digitally_shown_by"][0]
                    self.assertIn("images.memorix.nl", image["access_point"][0]["id"])
                    self.assertIn(
                        "localhost:8000/iiif/manifest/",
                        json.dumps(record["subject_of"], ensure_ascii=False),
                    )
                    return

        _skip_or_fail(self, "Record not found in export")

    def test_api_record(self):
        record = self._api_get_data(self._api_record_uri())
        self.assertEqual(record["member_of"][0]["type"], "Set")
        self.assertEqual(record["member_of"][0]["_label"], "Westfries Museum collection")
        self.assertEqual(record["current_owner"][0]["type"], "Group")
        self.assertEqual(record["current_owner"][0]["_label"], "Westfries Museum")
        self.assertTrue(record["member_of"][0].get("id"), "member_of should have a resolvable id")
        self.assertTrue(record["current_owner"][0].get("id"), "current_owner should have a resolvable id")

    def test_api_record_has_resolvable_collection_and_owner(self):
        record = self._api_get_data(self._api_record_uri())
        collection_uri = record["member_of"][0].get("id")
        owner_uri = record["current_owner"][0].get("id")

        self.assertTrue(collection_uri, "member_of should have a resolvable id")
        self.assertTrue(owner_uri, "current_owner should have a resolvable id")

        collection = self._api_get_data(collection_uri)
        self.assertEqual(collection["type"], "Set")
        self.assertEqual(collection["_label"], "Westfries Museum collection")

        owner = self._api_get_data(owner_uri)
        self.assertEqual(owner["type"], "Group")
        self.assertEqual(owner["_label"], "Westfries Museum")

    def test_api_search_finds_collection_and_owner(self):
        set_results = self._api_search("set", "Westfries Museum collection")
        self.assertTrue(
            any(
                item.get("type") == "Set"
                and self._api_get_data(item["id"]).get("_label") == "Westfries Museum collection"
                for item in set_results.get("orderedItems", [])
            ),
            "set search should return the Westfries Museum collection",
        )

        agent_results = self._api_search("agent", "Westfries Museum")
        self.assertTrue(
            any(
                item.get("type") == "Group"
                and self._api_get_data(item["id"]).get("_label") == "Westfries Museum"
                for item in agent_results.get("orderedItems", [])
            ),
            "agent search should return the Westfries Museum group",
        )


if __name__ == "__main__":
    unittest.main()
