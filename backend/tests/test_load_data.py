import tempfile
import unittest
from pathlib import Path

from scripts.load_data import _jsonl_lines, extract_search_text, text_value


class JsonlLinesTest(unittest.TestCase):
    def _write(self, content):
        tmp = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False)
        tmp.write(content)
        tmp.close()
        self.addCleanup(Path(tmp.name).unlink)
        return Path(tmp.name)

    def test_limit_caps_records_per_file(self):
        path = self._write('{"id": "a"}\n\n{"id": "b"}\n{"id": "c"}\n')
        self.assertEqual([line for _, line in _jsonl_lines(path, limit=2)], ['{"id": "a"}', '{"id": "b"}'])

    def test_no_limit_yields_all_non_empty_lines(self):
        path = self._write('{"id": "a"}\n\n{"id": "b"}\n')
        self.assertEqual([line for _, line in _jsonl_lines(path)], ['{"id": "a"}', '{"id": "b"}'])

    def test_limit_is_per_file(self):
        first = self._write('{"id": "a"}\n{"id": "b"}\n{"id": "c"}\n')
        second = self._write('{"id": "d"}\n{"id": "e"}\n{"id": "f"}\n{"id": "g"}\n')
        self.assertEqual(len(list(_jsonl_lines(first, limit=2))), 2)
        self.assertEqual(len(list(_jsonl_lines(second, limit=2))), 2)


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
