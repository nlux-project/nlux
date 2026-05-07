import json
import os
import subprocess
import unittest
from pathlib import Path
from urllib.parse import quote
# suppress NotOpenSSLWarning: urllib3
import warnings
warnings.filterwarnings("ignore", module="urllib3")

from pipeline.sources.museums.nha.c587.fetcher import COLLECTION_FILTER, NhaC587Fetcher
from pipeline.sources.museums.nha.c587.mapper import NhaC587Mapper


PIPELINE = Path(os.environ.get("PIPELINE_DIR", "/Users/lux/data-pipeline"))
FIXTURES = Path(__file__).parent / "fixtures"
TEST_NHA_C587_ID = os.environ.get("TEST_NHA_C587_ID", "F7DDF7EEFB8E11DF9E4D523BC2E286E2")
REQUIRE_LIVE = os.environ.get("NHA_C587_REQUIRE_LIVE") == "1"

RAW_REQUIRED_FIELDS = [
    "id",
    "asset",
    "metadata",
]

LINKED_ART_REQUIRED_FIELDS = [
    "identified_by",
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


def _about_people(record):
    return [
        entity
        for entity in record.get("about", [])
        if entity.get("type") == "Person"
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


class NhaC587PipelineIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.record = _load_json(FIXTURES / "nha-c587-record-F7DDF7.json")
        self.mapper = NhaC587Mapper(
            {
                "name": "nha-c587",
                "namespace": "https://hdl.handle.net/21.12102/",
                "all_configs": DummyConfigs(),
            }
        )

    def test_fetcher_builds_filtered_memorix_requests(self):
        fetcher = NhaC587Fetcher(
            {
                "name": "nha-c587",
                "fetch": "",
                "apiUrl": "https://webservices.memorix.nl/mediabank",
                "apiKey": "test-key",
                "all_configs": DummyConfigs(),
            }
        )

        self.assertTrue(fetcher.validate_identifier(TEST_NHA_C587_ID))
        self.assertEqual(
            fetcher.make_fetch_uri(TEST_NHA_C587_ID),
            f"https://webservices.memorix.nl/mediabank/media/{TEST_NHA_C587_ID}",
        )
        params = fetcher._params(include_filter=True, page=1, rows=25)
        self.assertEqual(params["apiKey"], "test-key")
        self.assertEqual(params["fq[]"], COLLECTION_FILTER)

    def test_fixture_has_required_raw_fields(self):
        self.assertEqual(_missing_fields(self.record, RAW_REQUIRED_FIELDS), [])

    def test_mapper_transforms_record(self):
        mapped = self.mapper.transform({"data": self.record})
        self.assertEqual(mapped["identifier"], TEST_NHA_C587_ID)
        self.assertEqual(mapped["source"], "nha-c587")

        data = mapped["data"]
        self.assertEqual(data["type"], "HumanMadeObject")
        self.assertEqual(data["_label"], "Portret van Cornelis van der Ploegh")
        self.assertEqual(_missing_fields(data, LINKED_ART_REQUIRED_FIELDS), [])
        self.assertEqual(data["member_of"][0]["_label"], "587 - portretten van de Provinciale Atlas Noord-Holland, Collectie van")
        self.assertEqual(data["current_owner"][0]["type"], "Group")
        self.assertEqual(data["current_owner"][0]["_label"], "Noord-Hollands Archief")
        self.assertEqual(data["current_location"]["type"], "Place")
        self.assertEqual(data["current_location"]["_label"], "Noord-Hollands Archief")
        self.assertIn("1680-01-01T00:00:00", json.dumps(data["produced_by"], ensure_ascii=False))
        self.assertIn("1875-12-31T23:59:59", json.dumps(data["produced_by"], ensure_ascii=False))
        self.assertIn("Chirurgijn in het Kennemerland", json.dumps(data["referred_to_by"], ensure_ascii=False))
        self.assertIn(
            "https://hdl.handle.net/21.12102/F7DDF7EEFB8E11DF9E4D523BC2E286E2",
            data["subject_of"][0]["digitally_carried_by"][0]["access_point"][0]["id"],
        )
        image = data["representation"][0]["digitally_shown_by"][0]
        self.assertEqual(image["format"], "image/jpeg")
        self.assertIn("images.memorix.nl/ranh", image["access_point"][0]["id"])
        self.assertIn(
            "localhost:8000/iiif/manifest/",
            json.dumps(data["subject_of"], ensure_ascii=False),
        )

    def test_mapper_extracts_portrait_title_subject_person(self):
        record = json.loads(json.dumps(self.record))
        cases = {
            "Portret van Maarten van Heemskerk": "Maarten van Heemskerk",
            "Portrait of Jane Doe": "Jane Doe",
            "Zelfportret van Judith Leyster": "Judith Leyster",
            "Selfportrait of Rembrandt van Rijn": "Rembrandt van Rijn",
            "Self-portrait of Vincent van Gogh": "Vincent van Gogh",
        }

        for title, expected in cases.items():
            with self.subTest(title=title):
                for item in record["metadata"]:
                    if item["field"] == "beschrijving":
                        item["value"] = title
                        break
                mapped = self.mapper.transform({"data": record})
                people = _about_people(mapped["data"])
                self.assertTrue(
                    any(person.get("_label") == expected for person in people),
                    f"{title!r} should link {expected!r} as an about Person",
                )

    def test_harvest_file(self):
        path = PIPELINE / "data" / "input" / "nha" / "c587" / f"{TEST_NHA_C587_ID}.json"
        if not path.exists():
            _skip_or_fail(self, f"Harvest file not found: {path}")

        record = _load_json(path)
        self.assertEqual(_missing_fields(record, RAW_REQUIRED_FIELDS), [])
        self.assertEqual(str(record.get("id")), TEST_NHA_C587_ID)

    def test_datacache_record(self):
        try:
            with _connect_pg(self) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT data FROM nha_c587_data_cache WHERE data->>'id' = %s", (TEST_NHA_C587_ID,))
                    row = cur.fetchone()
        except Exception as exc:
            _skip_or_fail(self, f"NHA C587 datacache table is unavailable: {exc}")

        if not row:
            _skip_or_fail(self, "Record not found in nha_c587_data_cache")

        record = _coerce_record(row[0])
        self.assertEqual(_missing_fields(record, RAW_REQUIRED_FIELDS), [])

    def test_reconciled_record(self):
        try:
            with _connect_pg(self) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT data FROM nha_c587_record_cache WHERE identifier = %s", (TEST_NHA_C587_ID,))
                    row = cur.fetchone()
        except Exception as exc:
            _skip_or_fail(self, f"NHA C587 record cache table is unavailable: {exc}")

        if not row:
            _skip_or_fail(self, "Record not found in nha_c587_record_cache")

        record = _coerce_record(row[0])
        self.assertEqual(_missing_fields(record, LINKED_ART_REQUIRED_FIELDS), [])

    def test_export_record(self):
        path = PIPELINE / "data" / "output" / "latest" / "export_nha-c587_0.jsonl"
        if not path.exists():
            _skip_or_fail(self, f"Export file not found: {path}")

        source_uri = f"hdl.handle.net/21.12102/{TEST_NHA_C587_ID}"
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                record = _coerce_record(json.loads(line))
                equivalents = record.get("equivalent", [])
                if any(source_uri in eq.get("id", "") for eq in equivalents):
                    self.assertEqual(_missing_fields(record, LINKED_ART_REQUIRED_FIELDS), [])
                    self.assertTrue(record["member_of"][0].get("id"), "member_of should have a resolvable id")
                    image = record["representation"][0]["digitally_shown_by"][0]
                    self.assertIn("images.memorix.nl/ranh", image["access_point"][0]["id"])
                    return

        _skip_or_fail(self, "Record not found in export")

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

    def test_api_mvanheemskerk_person_record(self):
        if not REQUIRE_LIVE:
            self.skipTest("live API test")

        results = self._api_search("agent", "Maarten van Heemskerk")
        people = [
            self._api_get_data(item["id"])
            for item in results.get("orderedItems", [])
            if item.get("type") == "Person" and item.get("id")
        ]

        self.assertTrue(people, "agent search should return a Person for Maarten van Heemskerk")
        self.assertTrue(
            any(person.get("_label") == "Maarten van Heemskerk" for person in people),
            "Maarten van Heemskerk should have a matching Person label",
        )


if __name__ == "__main__":
    unittest.main()
