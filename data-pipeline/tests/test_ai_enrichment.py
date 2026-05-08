import copy
import json
from pathlib import Path
import unittest

from pipeline.process.ai_enrichment import (
    AIEnrichmentError,
    AI_RESEARCH_CONCEPT,
    catalog_snapshot,
    has_ai_research_note,
    merge_ai_enrichment,
    sidecar_record,
    validate_sidecar_record,
)


class AIEnrichmentTest(unittest.TestCase):
    def setUp(self):
        self.record = {
            "id": "https://example.org/data/object/1355",
            "type": "HumanMadeObject",
            "_label": "Encyclopedie",
            "identified_by": [{"type": "Name", "content": "Encyclopedie"}],
            "classified_as": [{"type": "Type", "_label": "book"}],
            "referred_to_by": [{"type": "LinguisticObject", "content": "Existing note"}],
        }
        self.analysis = {
            "summary": "First edition encyclopedia set.",
            "catalog_snapshot": catalog_snapshot(self.record),
            "findings": [
                {
                    "severity": "major",
                    "title": "Volume count absent",
                    "detail": "The record does not state whether the set has all 35 volumes.",
                    "confidence": "high",
                }
            ],
            "sources": [{"title": "ARTFL", "url": "https://encyclopedie.uchicago.edu/"}],
            "raw_response_ref": "response-1",
        }

    def test_validate_valid_sidecar_record(self):
        record = sidecar_record(
            self.record,
            "teylers",
            "test-model",
            "ai-research-v1",
            self.analysis,
        )

        validate_sidecar_record(record)
        self.assertEqual(record["record_id"], self.record["id"])
        self.assertEqual(record["status"], "ok")

    def test_validate_ok_record_requires_sources(self):
        bad = sidecar_record(
            self.record,
            "teylers",
            "test-model",
            "ai-research-v1",
            {**self.analysis, "sources": [{"title": "placeholder"}]},
        )
        bad["sources"] = []

        with self.assertRaises(AIEnrichmentError):
            validate_sidecar_record(bad)

    def test_validate_error_record_can_have_no_sources(self):
        record = sidecar_record(
            self.record,
            "teylers",
            "test-model",
            "ai-research-v1",
            {**self.analysis, "sources": []},
            status="error",
            error="provider unavailable",
        )

        validate_sidecar_record(record)
        self.assertEqual(record["error"], "provider unavailable")

    def test_validate_rejects_malformed_finding_severity(self):
        bad = sidecar_record(
            self.record,
            "teylers",
            "test-model",
            "ai-research-v1",
            self.analysis,
        )
        bad["findings"][0]["severity"] = "critical"

        with self.assertRaises(AIEnrichmentError):
            validate_sidecar_record(bad)

    def test_merge_appends_ai_note_without_changing_catalog_fields(self):
        original = copy.deepcopy(self.record)
        sidecar = sidecar_record(
            self.record,
            "teylers",
            "test-model",
            "ai-research-v1",
            self.analysis,
        )

        merged = merge_ai_enrichment(self.record, sidecar, "http://localhost:8000/")

        self.assertEqual(self.record, original)
        self.assertEqual(merged["identified_by"], original["identified_by"])
        self.assertEqual(merged["classified_as"], original["classified_as"])
        self.assertEqual(len(merged["referred_to_by"]), 2)
        self.assertTrue(has_ai_research_note(merged))
        self.assertIn(
            f"data/concept/{AI_RESEARCH_CONCEPT}",
            merged["referred_to_by"][-1]["classified_as"][0]["id"],
        )
        self.assertIn("Volume count absent", merged["referred_to_by"][-1]["_content_html"])

    def test_merge_is_idempotent(self):
        sidecar = sidecar_record(
            self.record,
            "teylers",
            "test-model",
            "ai-research-v1",
            self.analysis,
        )

        merged_once = merge_ai_enrichment(self.record, sidecar, "http://localhost:8000/")
        merged_twice = merge_ai_enrichment(merged_once, sidecar, "http://localhost:8000/")

        self.assertEqual(len(merged_once["referred_to_by"]), len(merged_twice["referred_to_by"]))

    def test_teylers_1355_fixture_merges_expected_analysis_shape(self):
        fixture = Path(__file__).parent / "fixtures" / "ai-teylers-1355-sidecar.json"
        sidecar = json.loads(fixture.read_text(encoding="utf-8"))
        validate_sidecar_record(sidecar)

        merged = merge_ai_enrichment(self.record, sidecar, "http://localhost:8000/")

        html = merged["referred_to_by"][-1]["_content_html"]
        self.assertIn("No set description or volume count", html)
        self.assertIn("ARTFL Encyclopedie Project", html)
        self.assertIn("Generated 2026-03-07T00:00:00Z", html)


if __name__ == "__main__":
    unittest.main()
