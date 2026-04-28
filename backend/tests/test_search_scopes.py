import ast
from pathlib import Path
import unittest


class SearchScopesTest(unittest.TestCase):
    def test_event_scope_includes_pipeline_event_types(self):
        search_py = Path(__file__).parents[1] / "app" / "search.py"
        module = ast.parse(search_py.read_text())
        scope_types = None

        for node in module.body:
            if isinstance(node, ast.Assign):
                names = [target.id for target in node.targets if isinstance(target, ast.Name)]
                if "SCOPE_TYPES" in names:
                    scope_types = ast.literal_eval(node.value)
                    break
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                if node.target.id == "SCOPE_TYPES":
                    scope_types = ast.literal_eval(node.value)
                    break

        self.assertIsNotNone(scope_types)
        self.assertIn("Production", scope_types["event"])
        self.assertIn("Encounter", scope_types["event"])


if __name__ == "__main__":
    unittest.main()
