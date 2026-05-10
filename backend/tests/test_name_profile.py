import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.main import get_record


class _FakeQuery:
    def filter(self, *_args):
        return self

    def first(self):
        return SimpleNamespace(
            uri="http://localhost:8000/data/concept/abc",
            type="Type",
            label="prints (visual works)",
        )


class _FakeSession:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def query(self, *_args):
        return _FakeQuery()


class NameProfileTest(unittest.TestCase):
    def test_name_profile_uses_record_label(self):
        with patch("app.main.SessionLocal", return_value=_FakeSession()):
            result = get_record("concept/abc", profile="name")

        self.assertEqual(result["id"], "http://localhost:8000/data/concept/abc")
        self.assertEqual(result["type"], "Type")
        self.assertEqual(result["_label"], "prints (visual works)")
        self.assertEqual(result["identified_by"][0]["content"], "prints (visual works)")


if __name__ == "__main__":
    unittest.main()
