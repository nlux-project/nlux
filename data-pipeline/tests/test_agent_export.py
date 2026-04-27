import unittest

from pipeline.process.agent_export import (
    agent_uri,
    assign_agent_uris,
    build_agent_record,
)


class AgentExportTest(unittest.TestCase):
    def test_assign_agent_uris_collects_embedded_people(self):
        base_uri = "http://localhost:8000/"
        data = {
            "type": "HumanMadeObject",
            "produced_by": {
                "type": "Production",
                "carried_out_by": [{"type": "Person", "_label": "Bailliu, Pieter de"}],
            },
        }
        agents = {}

        assign_agent_uris(data, agents, base_uri)

        uri = agent_uri("Person", "Bailliu, Pieter de", base_uri)
        self.assertEqual(data["produced_by"]["carried_out_by"][0]["id"], uri)
        self.assertEqual(agents[uri], {"type": "Person", "label": "Bailliu, Pieter de"})

    def test_build_agent_record_creates_linked_art_person(self):
        uri = "http://localhost:8000/data/person/example"
        record = build_agent_record(uri, "Person", "Bailliu, Pieter de")

        self.assertEqual(record["id"], uri)
        self.assertEqual(record["type"], "Person")
        self.assertEqual(record["_label"], "Bailliu, Pieter de")
        self.assertEqual(record["identified_by"][0]["content"], "Bailliu, Pieter de")


if __name__ == "__main__":
    unittest.main()
