import importlib.util
from pathlib import Path
import sys
import unittest


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "ai-enrichment"
    / "ai-enrichment.py"
)
SPEC = importlib.util.spec_from_file_location("ai_enrichment_cli", SCRIPT_PATH)
ai_enrichment_cli = importlib.util.module_from_spec(SPEC)
sys.modules["ai_enrichment_cli"] = ai_enrichment_cli
SPEC.loader.exec_module(ai_enrichment_cli)


class AIEnrichmentCliTest(unittest.TestCase):
    def test_parse_checklist_reads_pending_and_done_items(self):
        items = ai_enrichment_cli.parse_checklist(
            "# objects\n"
            "[ ] 05477c72-b195-413c-afc6-1473fd31d317\n"
            "[X] done-object\n"
            "not a task\n"
        )

        self.assertEqual([item.object_id for item in items], ["05477c72-b195-413c-afc6-1473fd31d317", "done-object"])
        self.assertFalse(items[0].done)
        self.assertTrue(items[1].done)

    def test_mark_checklist_done_preserves_other_lines(self):
        checklist = "# objects\n[ ] first-object\n[X] second-object\n"

        updated = ai_enrichment_cli.mark_checklist_done(checklist, {"first-object"})

        self.assertEqual(updated, "# objects\n[X] first-object\n[X] second-object\n")

    def test_api_record_url_accepts_object_ids_and_full_urls(self):
        self.assertEqual(
            ai_enrichment_cli.api_record_url("http://localhost:8000", "abc 123"),
            "http://localhost:8000/data/object/abc%20123",
        )
        self.assertEqual(
            ai_enrichment_cli.api_record_url("http://localhost:8000", "http://localhost:8000/data/object/abc"),
            "http://localhost:8000/data/object/abc",
        )

    def test_extracts_image_and_manifest_urls(self):
        record = {
            "representation": [
                {
                    "digitally_shown_by": [
                        {"access_point": [{"id": "https://example.org/image.jpg"}]},
                    ]
                }
            ],
            "subject_of": [
                {
                    "digitally_carried_by": [
                        {"access_point": [{"id": "http://localhost:8000/iiif/manifest/token"}]},
                        {"access_point": [{"id": "https://museum.example/object/1"}]},
                    ]
                }
            ],
        }

        self.assertEqual(ai_enrichment_cli.extract_image_urls(record), ["https://example.org/image.jpg"])
        self.assertEqual(ai_enrichment_cli.extract_iiif_manifest_urls(record), ["http://localhost:8000/iiif/manifest/token"])
        self.assertEqual(ai_enrichment_cli.extract_web_pages(record), ["https://museum.example/object/1"])


if __name__ == "__main__":
    unittest.main()
