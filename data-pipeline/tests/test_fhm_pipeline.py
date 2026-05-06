import json
import os
import subprocess
import unittest
from pathlib import Path
from urllib.parse import quote
# suppress NotOpenSSLWarning: urllib3
import warnings
warnings.filterwarnings("ignore", module="urllib3")

from pipeline.sources.museums.fhm.fetcher import FhmFetcher
from pipeline.sources.museums.fhm.mapper import FhmMapper


PIPELINE = Path(os.environ.get("PIPELINE_DIR", "/Users/lux/data-pipeline"))
FIXTURES = Path(__file__).parent / "fixtures"
TEST_OBJECTID = os.environ.get("TEST_OBJECTID") or os.environ.get("TEST_PRIREF", "3")
FHM_COLLECTION_URI = "http://localhost:8000/data/set/4f324cd4-f0f2-552d-b0fd-681fda62d099"
WHENDRIKS_URI = "http://localhost:8000/data/person/5b6e8be2-3caf-5210-87e6-a5d53e10882d"
REQUIRE_LIVE = os.environ.get("FHM_REQUIRE_LIVE") == "1"

RAW_REQUIRED_FIELDS = [
    "objectid",
    "collection",
    "object_name",
    "titles",
    "artist",
    "dating",
    "material",
    "dimensions",
    "inventory_number",
    "deeplink",
]

LINKED_ART_REQUIRED_FIELDS = [
    "identified_by",
    "classified_as",
    "produced_by",
    "made_of",
    "dimension",
    "member_of",
    "current_owner",
    "current_location",
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
        self.allow_network = False
        self.globals = {}
        self.results = {"merged": {}}
        self.external = {}
        self.internal = {}

    def get_idmap(self):
        return DummyIdMap()

    def canonicalize(self, uri):
        return uri


class FhmPipelineIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.record = _load_json(FIXTURES / "fhm-record-3.json")
        self.mapper = FhmMapper(
            {
                "name": "fhm",
                "namespace": "http://collectie.franshalsmuseum.nl/?query=search=objectid=",
                "all_configs": DummyConfigs(),
            }
        )

    def _api_record_uri(self):
        source_uri = f"collectie.franshalsmuseum.nl/?query=search=objectid={TEST_OBJECTID}"
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

    def test_fetcher_builds_collection_connection_request(self):
        fetcher = FhmFetcher({"name": "fhm", "fetch": "", "all_configs": DummyConfigs()})

        self.assertTrue(fetcher.validate_identifier("3"))
        self.assertFalse(fetcher.validate_identifier("mf G 2000-5 b"))
        self.assertEqual(
            fetcher.make_fetch_uri("3"),
            "https://collectie.franshalsmuseum.nl/cc/ccConnector.asmx/search",
        )

        spec = fetcher.make_search_spec("3")
        self.assertEqual(spec["ccSettingsName"], "Alternative")
        self.assertEqual(spec["showtype"], "record")
        self.assertEqual(spec["numPerPage"], 1)
        self.assertEqual(spec["first"], 1)
        self.assertIn({"id": 0, "tag": "objectid", "value": "3"}, spec["searchValues"])

    def test_fixture_has_required_raw_fields(self):
        self.assertEqual(_missing_fields(self.record, RAW_REQUIRED_FIELDS), [])

    def test_mapper_transforms_record(self):
        mapped = self.mapper.transform({"data": self.record})
        self.assertEqual(mapped["identifier"], "3")
        self.assertEqual(mapped["source"], "fhm")

        data = mapped["data"]
        self.assertEqual(data["type"], "HumanMadeObject")
        self.assertEqual(data["_label"], "I love you")
        self.assertEqual(_missing_fields(data, LINKED_ART_REQUIRED_FIELDS), [])
        self.assertEqual(data["member_of"][0]["_label"], "Frans Hals Museum collection")
        self.assertEqual(data["current_owner"][0]["id"], "http://www.wikidata.org/entity/Q574961")
        self.assertEqual(data["current_location"]["type"], "Place")
        self.assertEqual(data["current_location"]["_label"], "Frans Hals Museum")
        self.assertEqual(
            data["current_location"]["id"],
            "http://localhost:8000/data/place/68c89848-21ad-5bed-8546-4e249b35924d",
        )
        self.assertEqual(data["produced_by"]["carried_out_by"][0]["_label"], "Luuk Wilmering")
        self.assertIn("mf G 2000-5 b", json.dumps(data["identified_by"], ensure_ascii=False))
        self.assertIn("foto", json.dumps(data["made_of"], ensure_ascii=False).lower())
        self.assertIn("113", json.dumps(data["dimension"], ensure_ascii=False))
        self.assertIn(
            "collectie.franshalsmuseum.nl/?query=search=objectid=3",
            data["subject_of"][0]["digitally_carried_by"][0]["access_point"][0]["id"],
        )
        self.assertIn("imageproxy.ashx", json.dumps(data["representation"], ensure_ascii=False))

    def test_harvest_file(self):
        path = PIPELINE / "data" / "input" / "fhm" / f"{TEST_OBJECTID}.json"
        if not path.exists():
            _skip_or_fail(self, f"Harvest file not found: {path}")

        record = _load_json(path)
        self.assertEqual(_missing_fields(record, RAW_REQUIRED_FIELDS), [])
        self.assertEqual(str(record.get("objectid")), TEST_OBJECTID)

    def test_datacache_record(self):
        try:
            with _connect_pg(self) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT data FROM fhm_data_cache WHERE data->>'objectid' = %s", (TEST_OBJECTID,))
                    row = cur.fetchone()
        except Exception as exc:
            _skip_or_fail(self, f"FHM datacache table is unavailable: {exc}")

        if not row:
            _skip_or_fail(self, "Record not found in fhm_data_cache")

        record = _coerce_record(row[0])
        self.assertEqual(_missing_fields(record, RAW_REQUIRED_FIELDS), [])

    def test_reconciled_record(self):
        try:
            with _connect_pg(self) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT data FROM fhm_record_cache WHERE identifier = %s", (TEST_OBJECTID,))
                    row = cur.fetchone()
        except Exception as exc:
            _skip_or_fail(self, f"FHM record cache table is unavailable: {exc}")

        if not row:
            _skip_or_fail(self, "Record not found in fhm_record_cache")

        record = _coerce_record(row[0])
        self.assertEqual(_missing_fields(record, LINKED_ART_REQUIRED_FIELDS), [])

    def test_rewritten_record(self):
        try:
            with _connect_pg(self) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT data FROM fhm_rewritten_record_cache "
                        "WHERE data::text LIKE %s LIMIT 1",
                        (f"%objectid={TEST_OBJECTID}%",),
                    )
                    row = cur.fetchone()
        except Exception as exc:
            _skip_or_fail(self, f"FHM rewritten record cache table is unavailable: {exc}")

        if not row:
            _skip_or_fail(self, "Record not found in fhm_rewritten_record_cache")

        record = _coerce_record(row[0])
        self.assertEqual(_missing_fields(record, LINKED_ART_REQUIRED_FIELDS), [])

    def test_export_record(self):
        path = PIPELINE / "data" / "output" / "latest" / "export_fhm_0.jsonl"
        if not path.exists():
            _skip_or_fail(self, f"Export file not found: {path}")

        source_uri = f"collectie.franshalsmuseum.nl/?query=search=objectid={TEST_OBJECTID}"
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
        self.assertEqual(record["member_of"][0]["type"], "Set")
        self.assertEqual(record["member_of"][0]["_label"], "Frans Hals Museum collection")
        self.assertEqual(record["current_owner"][0]["type"], "Group")
        self.assertEqual(record["current_owner"][0]["_label"], "Frans Hals Museum")
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
        self.assertEqual(collection["_label"], "Frans Hals Museum collection")

        owner = self._api_get_data(owner_uri)
        self.assertEqual(owner["type"], "Group")
        self.assertEqual(owner["_label"], "Frans Hals Museum")

    def test_api_search_finds_collection_and_owner(self):
        set_results = self._api_search("set", "Frans Hals Museum collection")
        self.assertTrue(
            any(
                item.get("type") == "Set"
                and self._api_get_data(item["id"]).get("_label") == "Frans Hals Museum collection"
                for item in set_results.get("orderedItems", [])
            ),
            "set search should return the Frans Hals Museum collection",
        )

        agent_results = self._api_search("agent", "Frans Hals Museum")
        self.assertTrue(
            any(
                item.get("type") == "Group"
                and self._api_get_data(item["id"]).get("_label") == "Frans Hals Museum"
                for item in agent_results.get("orderedItems", [])
            ),
            "agent search should return the Frans Hals Museum group",
        )

    def test_api_fhm_collection_record(self):
        record = self._api_get_data(FHM_COLLECTION_URI)

        self.assertEqual(record["id"], FHM_COLLECTION_URI)
        self.assertEqual(record["type"], "Set")
        self.assertEqual(record["_label"], "Frans Hals Museum collection")
        self.assertIn("Frans Hals Museum collection", _identified_by_content(record))
        self.assertTrue(
            _has_classification(
                record,
                label="Named Collection",
                equivalent_id="http://vocab.getty.edu/aat/300456764",
            ),
            "collection should be classified as a named collection",
        )

    def test_api_whendriks_person_record(self):
        record = self._api_get_data(WHENDRIKS_URI)

        self.assertEqual(record["id"], WHENDRIKS_URI)
        self.assertEqual(record["type"], "Person")
        self.assertEqual(record["_label"], "Wybrand Hendriks")
        self.assertIn("Wybrand Hendriks", _identified_by_content(record))

        born_timespan = record.get("born", {}).get("timespan", {})
        died_timespan = record.get("died", {}).get("timespan", {})
        self.assertTrue(born_timespan, "birth timespan should be present")
        self.assertTrue(died_timespan, "death timespan should be present")
        self.assertEqual(born_timespan.get("end_of_the_end"), "1744-12-31T23:59:59")
        self.assertEqual(died_timespan.get("end_of_the_end"), "1831-12-31T23:59:59")

        notes = record.get("referred_to_by", []) or []
        biography_notes = [
            note for note in notes
            if note.get("content")
            and _has_classification(note, equivalent_id="http://vocab.getty.edu/aat/300080102")
        ]
        self.assertTrue(biography_notes, "biography should be present")
        self.assertTrue(
            any("Wikipedia summary" in " ".join(_identified_by_content(note)) for note in notes),
            "Wikipedia summary should be present",
        )


if __name__ == "__main__":
    unittest.main()
