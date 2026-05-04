import json
import os
import subprocess
import unittest
from pathlib import Path
# suppress NotOpenSSLWarning: urllib3
import warnings
warnings.filterwarnings("ignore", module="urllib3")

from pipeline.sources.museums.teylers.mapper import TeylersMapper


PIPELINE = Path(os.environ.get("PIPELINE_DIR", "/Users/lux/data-pipeline"))
TEST_PRIREF = os.environ.get("TEST_PRIREF", "41634")
REQUIRE_LIVE = os.environ.get("TEYLERS_REQUIRE_LIVE") == "1"

RAW_REQUIRED_FIELDS = [
    "Title",
    "Description",
    "Dimension",
    "Material",
    "Production",
    "Object_category",
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
        if TEST_PRIREF == "21916":
            _assert_teylers_image_url(self, record)
            _assert_teylers_iiif_manifest(self, record)

        for person in record.get("produced_by", {}).get("carried_out_by", []):
            self.assertIn("id", person, f"agent {person.get('_label')} has no id")


if __name__ == "__main__":
    unittest.main()
