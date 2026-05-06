import json
import os
import subprocess
import unittest
from pathlib import Path
from urllib.parse import quote
# suppress NotOpenSSLWarning: urllib3
import warnings
warnings.filterwarnings("ignore", module="urllib3")

from pipeline.sources.museums.teylers.mapper import TeylersMapper


PIPELINE = Path(os.environ.get("PIPELINE_DIR", "/Users/lux/data-pipeline"))
TEST_PRIREF = os.environ.get("TEST_PRIREF", "41634")
TEYLERS_COLLECTION_URI = "http://localhost:8000/data/set/d435a0f6-1837-5d39-a545-f9b994e8464c"
BAILLIU_URI = "http://localhost:8000/data/person/dea612fd-103f-539a-85a2-20a9eb44ad0d"
REQUIRE_LIVE = os.environ.get("TEYLERS_REQUIRE_LIVE") == "1"

RAW_REQUIRED_FIELDS = [
    "Title",
    "Description",
    "Dimension",
    "Material",
    "Production",
    "Object_name",
    "Technique",
]

LINKED_ART_REQUIRED_FIELDS = [
    "identified_by",
    "referred_to_by",
    "classified_as",
    "produced_by",
    "made_of",
    "member_of",
    "dimension",
    "current_owner",
    "subject_of",
    "representation",
]


def _representation_image_urls(record):
    urls = []
    for rep in record.get("representation", []):
        for digital in rep.get("digitally_shown_by", []):
            if digital.get("id"):
                urls.append(digital["id"])
            for access_point in digital.get("access_point", []):
                if access_point.get("id"):
                    urls.append(access_point["id"])
    return urls


def _iiif_manifest_urls(record):
    urls = []
    for subject in record.get("subject_of", []):
        for digital in subject.get("digitally_carried_by", []):
            conforms_to = digital.get("conforms_to", [])
            if not any("iiif.io/api/presentation/3" in entry.get("id", "") for entry in conforms_to):
                continue
            for access_point in digital.get("access_point", []):
                if access_point.get("id"):
                    urls.append(access_point["id"])
    return urls


def _assert_teylers_image_url(testcase, record):
    urls = _representation_image_urls(record)
    testcase.assertTrue(urls, "record has no image URL in representation")
    testcase.assertTrue(
        any("teylers.adlibhosting.com" in url for url in urls),
        f"record image URLs are not Teylers URLs: {urls}",
    )


def _assert_teylers_iiif_manifest(testcase, record):
    urls = _iiif_manifest_urls(record)
    testcase.assertTrue(urls, "record has no IIIF manifest in subject_of")
    testcase.assertTrue(
        any("/iiif/manifest/" in url for url in urls),
        f"record IIIF manifest URLs are not NLUX manifest URLs: {urls}",
    )


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
    internal_uri = "http://localhost:8000/data/"
    data_dir = str(Path(__file__).parent / "fixtures")
    allow_network = False
    globals = {}
    results = {"merged": {}}
    external = {}
    internal = {}

    def get_idmap(self):
        return DummyIdMap()

    def canonicalize(self, uri):
        return uri


def _about_people(record):
    return [
        entity
        for entity in record.get("about", [])
        if entity.get("type") == "Person"
    ]


class TeylersPipelineIntegrationTest(unittest.TestCase):
    def _api_record_uri(self):
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
                        f"('%museum/{TEST_PRIREF}%',))\n"
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

    def test_mapper_extracts_portrait_subject_person(self):
        mapper = TeylersMapper(
            {
                "name": "teylers",
                "namespace": "https://teylers.adlibhosting.com/ais6/Details/museum/",
                "all_configs": DummyConfigs(),
            }
        )
        mapped = mapper.transform(
            {
                "data": {
                    "@priref": "5569",
                    "Title": [{"title": {"spans": [{"text": "Portret Jacobus Zaffius"}]}}],
                    "Object_name": [{"object_name": {"spans": [{"text": "grafiek"}]}}],
                    "Production": [
                        {"creator": {"spans": [{"text": "Velde, Jan van de (II) (1593-1641)"}]}}
                    ],
                    "Content_subject": [
                        {"content.subject": {"spans": [{"text": "portret (Zaffius, Jacobus)"}]}},
                        {"content.subject": {"spans": [{"text": "vanitas"}]}},
                    ],
                }
            }
        )

        people = _about_people(mapped["data"])
        self.assertEqual([person["_label"] for person in people], ["Jacobus Zaffius"])

    def test_harvest_file(self):
        path = PIPELINE / "data" / "input" / "teylers" / f"{TEST_PRIREF}.json"
        if not path.exists():
            _skip_or_fail(self, f"Harvest file not found: {path}")

        record = _load_json(path)
        missing = _missing_fields(record, ["@priref", "@created", "@modification", *RAW_REQUIRED_FIELDS])
        self.assertEqual(missing, [])

    def test_datacache_record(self):
        with _connect_pg(self) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT data FROM teylers_data_cache WHERE data->>'@priref' = %s", (TEST_PRIREF,))
                row = cur.fetchone()

        if not row:
            _skip_or_fail(self, "Record not found in teylers_data_cache")

        record = _coerce_record(row[0])
        self.assertEqual(_missing_fields(record, RAW_REQUIRED_FIELDS), [])

    def test_reconciled_record(self):
        with _connect_pg(self) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT data FROM teylers_record_cache WHERE identifier = %s", (TEST_PRIREF,))
                row = cur.fetchone()

        if not row:
            _skip_or_fail(self, "Record not found in teylers_record_cache")

        record = _coerce_record(row[0])
        self.assertEqual(_missing_fields(record, LINKED_ART_REQUIRED_FIELDS), [])
        if TEST_PRIREF in {"5569", "24573"}:
            self.assertTrue(
                any("Zaffius" in person.get("_label", "") for person in _about_people(record)),
                "Zaffius portrait records should link the sitter as an about Person",
            )
        if TEST_PRIREF == "21916":
            _assert_teylers_image_url(self, record)
            _assert_teylers_iiif_manifest(self, record)

    def test_rewritten_record(self):
        with _connect_pg(self) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT data FROM teylers_rewritten_record_cache "
                    "WHERE data::text LIKE %s LIMIT 1",
                    (f"%museum/{TEST_PRIREF}%",),
                )
                row = cur.fetchone()

        if not row:
            _skip_or_fail(self, "Record not found in teylers_rewritten_record_cache")

        record = _coerce_record(row[0])
        self.assertEqual(_missing_fields(record, LINKED_ART_REQUIRED_FIELDS), [])
        if TEST_PRIREF == "21916":
            _assert_teylers_image_url(self, record)
            _assert_teylers_iiif_manifest(self, record)

    def test_export_record(self):
        path = PIPELINE / "data" / "output" / "latest" / "export_teylers_0.jsonl"
        if not path.exists():
            _skip_or_fail(self, f"Export file not found: {path}")

        with path.open(encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                record = _coerce_record(json.loads(line))
                equivalents = record.get("equivalent", [])
                if any(f"museum/{TEST_PRIREF}" in eq.get("id", "") for eq in equivalents):
                    required = [
                        "identified_by",
                        "produced_by",
                        "made_of",
                        "dimension",
                        "classified_as",
                        "current_owner",
                        "representation",
                    ]
                    self.assertEqual(_missing_fields(record, required), [])
                    if TEST_PRIREF == "21916":
                        _assert_teylers_image_url(self, record)
                        _assert_teylers_iiif_manifest(self, record)
                    return

        _skip_or_fail(self, "Record not found in export")

    def test_api_record(self):
        record = self._api_get_data(self._api_record_uri())
        self.assertEqual(_missing_fields(record, [*LINKED_ART_REQUIRED_FIELDS, "_links"]), [])
        if TEST_PRIREF == "21916":
            _assert_teylers_image_url(self, record)
            _assert_teylers_iiif_manifest(self, record)

        for person in record.get("produced_by", {}).get("carried_out_by", []):
            self.assertIn("id", person, f"agent {person.get('_label')} has no id")

    def test_api_record_has_resolvable_collection_and_owner(self):
        record = self._api_get_data(self._api_record_uri())
        collection_uri = record["member_of"][0].get("id")
        owner_uri = record["current_owner"][0].get("id")

        self.assertTrue(collection_uri, "member_of should have a resolvable id")
        self.assertTrue(owner_uri, "current_owner should have a resolvable id")

        collection = self._api_get_data(collection_uri)
        self.assertEqual(collection["type"], "Set")
        self.assertEqual(collection["_label"], "Teylers Museum collection")

        owner = self._api_get_data(owner_uri)
        self.assertEqual(owner["type"], "Group")
        self.assertEqual(owner["_label"], "Teylers Museum")

    def test_api_search_finds_collection_and_owner(self):
        set_results = self._api_search("set", "Teylers Museum collection")
        self.assertTrue(
            any(
                item.get("type") == "Set"
                and self._api_get_data(item["id"]).get("_label") == "Teylers Museum collection"
                for item in set_results.get("orderedItems", [])
            ),
            "set search should return the Teylers Museum collection",
        )

        agent_results = self._api_search("agent", "Teylers Museum")
        self.assertTrue(
            any(
                item.get("type") == "Group"
                and self._api_get_data(item["id"]).get("_label") == "Teylers Museum"
                for item in agent_results.get("orderedItems", [])
            ),
            "agent search should return the Teylers Museum group",
        )

    def test_api_teylers_collection_record(self):
        record = self._api_get_data(TEYLERS_COLLECTION_URI)

        self.assertEqual(record["id"], TEYLERS_COLLECTION_URI)
        self.assertEqual(record["type"], "Set")
        self.assertEqual(record["_label"], "Teylers Museum collection")
        self.assertIn("Teylers Museum collection", _identified_by_content(record))
        self.assertTrue(
            _has_classification(
                record,
                label="Named Collection",
                equivalent_id="http://vocab.getty.edu/aat/300456764",
            ),
            "collection should be classified as a named collection",
        )

    def test_api_bailliu_person_record(self):
        record = self._api_get_data(BAILLIU_URI)

        self.assertEqual(record["id"], BAILLIU_URI)
        self.assertEqual(record["type"], "Person")
        self.assertEqual(record["_label"], "Bailliu, Peeter-Frans (graveur) (m)")
        self.assertIn("Bailliu, Peeter-Frans (graveur) (m)", _identified_by_content(record))


if __name__ == "__main__":
    unittest.main()
