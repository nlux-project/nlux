import unittest

from scripts.enrich_person_biographies import (
    BIOGRAPHY_CONCEPT,
    biography_note,
    has_biography_note,
    label_variants,
    normalise_label,
)


class EnrichPersonBiographiesTest(unittest.TestCase):
    def test_label_variants_include_inverted_name(self):
        self.assertEqual(
            label_variants("Bailliu, Pieter de"),
            ["Bailliu, Pieter de", "Pieter de Bailliu"],
        )

    def test_normalise_label_removes_punctuation_and_case(self):
        self.assertEqual(
            normalise_label("Bailliu, Pieter de (1613-1660)"),
            "bailliu pieter de",
        )

    def test_biography_note_uses_display_biography_classification(self):
        note = biography_note(
            {
                "extract": "Pieter de Bailliu was a Flemish engraver.",
                "page_url": "https://en.wikipedia.org/wiki/Pieter_de_Bailliu",
                "title": "Pieter de Bailliu",
                "language": "en",
            },
            "http://localhost:8000/",
        )

        self.assertEqual(
            note["content"],
            "Pieter de Bailliu was a Flemish engraver.",
        )
        self.assertTrue(has_biography_note({"referred_to_by": [note]}))
        self.assertEqual(
            note["classified_as"][0]["id"],
            f"http://localhost:8000/data/concept/{BIOGRAPHY_CONCEPT}",
        )
        self.assertEqual(note["language"][0]["_label"], "English")
        self.assertEqual(
            note["subject_of"][0]["digitally_carried_by"][0]["access_point"][0]["id"],
            "https://en.wikipedia.org/wiki/Pieter_de_Bailliu",
        )


if __name__ == "__main__":
    unittest.main()
