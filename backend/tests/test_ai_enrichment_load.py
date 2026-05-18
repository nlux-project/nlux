import os
import unittest

from scripts.search_text import AI_RESEARCH_CONCEPT, extract_search_text
from scripts.load_ai_enrichment import candidate_record_uris


class AIEnrichmentLoadTest(unittest.TestCase):
    def setUp(self):
        os.environ.pop("NLUX_INDEX_AI_ENRICHMENT", None)
        self.doc = {
            "_label": "Catalog title",
            "identified_by": [{"content": "Object 1355"}],
            "referred_to_by": [
                {"content": "Regular catalog note"},
                {
                    "content": "AI-only research finding",
                    "classified_as": [
                        {
                            "id": f"http://localhost:8000/data/concept/{AI_RESEARCH_CONCEPT}",
                            "_label": "AI Research Analysis",
                        }
                    ],
                },
            ],
        }

    def tearDown(self):
        os.environ.pop("NLUX_INDEX_AI_ENRICHMENT", None)

    def test_ai_enrichment_note_is_not_indexed_by_default(self):
        text = extract_search_text(self.doc)

        self.assertIn("Regular catalog note", text)
        self.assertNotIn("AI-only research finding", text)

    def test_ai_enrichment_note_can_be_indexed_by_env_flag(self):
        os.environ["NLUX_INDEX_AI_ENRICHMENT"] = "1"

        text = extract_search_text(self.doc)

        self.assertIn("AI-only research finding", text)

    def test_candidate_record_uris_matches_local_api_base(self):
        self.assertEqual(
            candidate_record_uris(
                "https://nlux.local/data/object/05477c72-b195-413c-afc6-1473fd31d317",
                "http://localhost:8000",
            ),
            [
                "https://nlux.local/data/object/05477c72-b195-413c-afc6-1473fd31d317",
                "http://localhost:8000/data/object/05477c72-b195-413c-afc6-1473fd31d317",
            ],
        )


if __name__ == "__main__":
    unittest.main()
