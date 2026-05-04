import unittest

from scripts.generate_agents import _assign_uris


class GenerateAgentsTest(unittest.TestCase):
    def test_assign_uris_uses_known_museum_group_authorities(self):
        base_uri = "http://localhost:8000/"
        data = {
            "type": "HumanMadeObject",
            "current_owner": [{"type": "Group", "_label": "Frans Hals Museum"}],
        }
        agents = {}

        changed = _assign_uris(data, agents, base_uri)

        owner_uri = data["current_owner"][0]["id"]
        self.assertTrue(changed)
        self.assertEqual(owner_uri, "http://www.wikidata.org/entity/Q574961")
        self.assertEqual(agents[owner_uri]["type"], "Group")
        self.assertEqual(agents[owner_uri]["label"], "Frans Hals Museum")


if __name__ == "__main__":
    unittest.main()
