import json
import tempfile
import unittest
from pathlib import Path

from scripts.check_api_fields import get_field, load_config


class CheckApiFieldsTest(unittest.TestCase):
    def test_get_field_supports_nested_objects_lists_and_json_pointer(self):
        document = {
            "type": "HumanMadeObject",
            "identified_by": [{"content": "Example title"}],
            "nested/key": {"~value": 42},
        }

        self.assertEqual(get_field(document, "type"), "HumanMadeObject")
        self.assertEqual(get_field(document, "identified_by[0].content"), "Example title")
        self.assertEqual(get_field(document, "/nested~1key/~0value"), 42)

    def test_load_config_accepts_multiple_field_styles(self):
        config = {
            "checks": [
                {
                    "url": "http://example.test/one",
                    "field": "type",
                    "value": "HumanMadeObject",
                },
                {
                    "url": "http://example.test/two",
                    "fields": [{"field": "id", "value": "abc"}],
                    "field_values": {"_label": "Title"},
                },
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "checks.json"
            path.write_text(json.dumps(config), encoding="utf-8")
            checks = load_config(path)

        self.assertEqual(len(checks), 2)
        self.assertEqual(checks[0].fields[0].field, "type")
        self.assertEqual(checks[1].fields[0].field, "id")
        self.assertEqual(checks[1].fields[1].field, "_label")


if __name__ == "__main__":
    unittest.main()
