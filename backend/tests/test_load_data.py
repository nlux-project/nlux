import unittest

from scripts.load_data import extract_search_text, text_value


class LoadDataTest(unittest.TestCase):
    def test_text_value_flattens_list_labels(self):
        self.assertEqual(text_value(["De Nachtwacht", "The Night Watch"]), "De Nachtwacht The Night Watch")

    def test_extract_search_text_handles_non_string_values(self):
        doc = {
            "_label": ["De Nachtwacht", "The Night Watch"],
            "identified_by": [{"content": ["SK-C-5", "RMA accession"]}],
            "referred_to_by": [{"content": {"content": "Beschrijving"}}],
        }

        self.assertEqual(
            extract_search_text(doc),
            "De Nachtwacht The Night Watch SK-C-5 RMA accession Beschrijving",
        )


if __name__ == "__main__":
    unittest.main()
