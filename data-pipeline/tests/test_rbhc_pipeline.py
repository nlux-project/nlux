import json
import os
import subprocess
import unittest
from pathlib import Path
from urllib.parse import quote

import warnings
warnings.filterwarnings("ignore", module="urllib3")

from pipeline.sources.museums.rbhc.fetcher import RbhcFetcher
from pipeline.sources.museums.rbhc.mapper import RbhcMapper


PIPELINE = Path(os.environ.get("PIPELINE_DIR", "/Users/lux/data-pipeline"))
FIXTURES = Path(__file__).parent / "fixtures"
TEST_PRIREF = os.environ.get("TEST_PRIREF", "2")
RBHC_COLLECTION_URI = "http://localhost:8000/data/set/d1096be6-e742-5ad7-ac17-1fe71ac0a49e"
RBHC_OWNER_URI = "http://www.wikidata.org/entity/Q759169"
LENOIR_URI = "http://localhost:8000/data/person/858f1a1f-6039-53d3-80f0-c48bb68f5a61"
REQUIRE_LIVE = os.environ.get("RBHC_REQUIRE_LIVE") == "1"

RAW_REQUIRED_FIELDS = [
    "@priref",
    "@created",
    "@modification",
    "Title",
    "Object_name",
    "Production",
    "Production_date",
    "Description",
    "Dimension",
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
    "referred_to_by",
    "subject_of",
    "representation",
]

DESCRIPTION_STATEMENT = "http://vocab.getty.edu/aat/300435416"


def _classified_as_equivalent(record, uri):
    for cls in record.get("classified_as", []):
        if cls.get("id") == uri:
            return True
        if any(eq.get("id") == uri for eq in cls.get("equivalent", [])):
            return True
    return False


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


def _description_notes(record):
    return [
        note
        for note in record.get("referred_to_by", [])
        if note.get("content") and _classified_as_equivalent(note, DESCRIPTION_STATEMENT)
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

    def _api_record_uri(self):
        source_uri = f"https://mmb-web.adlibhosting.com/ais6/Details/collect/{TEST_PRIREF}"
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
                        f"('%\"id\": \"{source_uri}\"%',))\n"
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
        descriptions = _description_notes(data)
        self.assertEqual(len(descriptions), 1)
        self.assertIn("Geelkoperen standaardmeter", descriptions[0]["content"])
        self.assertIn("mmb-web.adlibhosting.com/ais6/Details/collect/2", data["subject_of"][0]["digitally_carried_by"][0]["access_point"][0]["id"])
        self.assertIn(
            "localhost:8000/iiif/manifest/",
            json.dumps(data["subject_of"], ensure_ascii=False),
        )
        image_url = data["representation"][0]["digitally_shown_by"][0]["access_point"][0]["id"]
        self.assertIn("Website%5CVoorwerpen", image_url.replace("\\", "%5C"))

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
        descriptions = record.get("Description", [])
        self.assertTrue(
            any("zonnewijzer" in json.dumps(desc, ensure_ascii=False).lower() for desc in descriptions)
            or TEST_PRIREF != "246"
        )

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
        self.assertTrue(_description_notes(record))

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
        path = PIPELINE / "data" / "output" / "latest" / "export_rbhc_0.jsonl"
        if not path.exists():
            _skip_or_fail(self, f"Export file not found: {path}")

        source_uri = f"https://mmb-web.adlibhosting.com/ais6/Details/collect/{TEST_PRIREF}"
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                record = _coerce_record(json.loads(line))
                equivalents = record.get("equivalent", [])
                if any(eq.get("id", "").rstrip("/") == source_uri for eq in equivalents):
                    self.assertEqual(_missing_fields(record, LINKED_ART_REQUIRED_FIELDS), [])
                    self.assertTrue(_description_notes(record))
                    return

        _skip_or_fail(self, "Record not found in export")

    def test_api_record(self):
        record = self._api_get_data(self._api_record_uri())
        self.assertEqual(_missing_fields(record, [*LINKED_ART_REQUIRED_FIELDS, "_links"]), [])
        self.assertTrue(_description_notes(record))

    def test_api_record_has_resolvable_collection_and_owner(self):
        record = self._api_get_data(self._api_record_uri())
        collection_uri = record["member_of"][0].get("id")
        owner_uri = record["current_owner"][0].get("id")

        self.assertTrue(collection_uri, "member_of should have a resolvable id")
        self.assertTrue(owner_uri, "current_owner should have a resolvable id")

        collection = self._api_get_data(collection_uri)
        self.assertEqual(collection["type"], "Set")
        self.assertEqual(collection["_label"], "Rijksmuseum Boerhaave collection")

        owner = self._api_get_data(owner_uri)
        self.assertEqual(owner["type"], "Group")
        self.assertEqual(owner["_label"], "Rijksmuseum Boerhaave")

    def test_api_search_finds_collection_and_owner(self):
        set_results = self._api_search("set", "Rijksmuseum Boerhaave collection")
        self.assertTrue(
            any(
                item.get("type") == "Set"
                and self._api_get_data(item["id"]).get("_label") == "Rijksmuseum Boerhaave collection"
                for item in set_results.get("orderedItems", [])
            ),
            "set search should return the Rijksmuseum Boerhaave collection",
        )

        agent_results = self._api_search("agent", "Rijksmuseum Boerhaave")
        self.assertTrue(
            any(
                item.get("type") == "Group"
                and self._api_get_data(item["id"]).get("_label") == "Rijksmuseum Boerhaave"
                for item in agent_results.get("orderedItems", [])
            ),
            "agent search should return the Rijksmuseum Boerhaave group",
        )

    def test_api_rbhc_collection_record(self):
        record = self._api_get_data(RBHC_COLLECTION_URI)

        self.assertEqual(record["id"], RBHC_COLLECTION_URI)
        self.assertEqual(record["type"], "Set")
        self.assertEqual(record["_label"], "Rijksmuseum Boerhaave collection")
        self.assertIn("Rijksmuseum Boerhaave collection", _identified_by_content(record))
        self.assertTrue(
            _has_classification(
                record,
                label="Named Collection",
                equivalent_id="http://vocab.getty.edu/aat/300456764",
            ),
            "collection should be classified as a named collection",
        )

    def test_api_lenoir_person_record(self):
        record = self._api_get_data(LENOIR_URI)

        self.assertEqual(record["id"], LENOIR_URI)
        self.assertEqual(record["type"], "Person")
        self.assertEqual(record["_label"], "Lenoir, Etienne")
        self.assertIn("Lenoir, Etienne", _identified_by_content(record))

        born_timespan = record.get("born", {}).get("timespan", {})
        died_timespan = record.get("died", {}).get("timespan", {})
        self.assertTrue(born_timespan, "birth timespan should be present")
        self.assertTrue(died_timespan, "death timespan should be present")
        self.assertEqual(born_timespan.get("end_of_the_end"), "1822-12-31T23:59:59")
        self.assertEqual(died_timespan.get("end_of_the_end"), "1900-12-31T23:59:59")


if __name__ == "__main__":
    unittest.main()
