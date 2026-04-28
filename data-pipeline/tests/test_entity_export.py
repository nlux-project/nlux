import unittest

from pipeline.process.entity_export import (
    assign_entity_uris,
    build_entity_record,
    entity_uri,
)


class EntityExportTest(unittest.TestCase):
    def test_assign_entity_uris_collects_searchable_embedded_entities(self):
        base_uri = "http://localhost:8000/"
        data = {
            "type": "HumanMadeObject",
            "classified_as": [{"type": "Type", "_label": "coins (money)"}],
            "made_of": [{"type": "Material", "_label": "Brons"}],
            "current_location": {"type": "Place", "_label": "Depot C"},
            "member_of": [{"type": "Set", "_label": "Huis van Hilde collection"}],
            "produced_by": {
                "type": "Production",
                "carried_out_by": [{"type": "Person", "_label": "Rembrandt"}],
            },
        }
        entities = {}

        assign_entity_uris(data, entities, base_uri)

        labels = {info["label"] for info in entities.values()}
        self.assertIn("coins (money)", labels)
        self.assertIn("Brons", labels)
        self.assertIn("Depot C", labels)
        self.assertIn("Huis van Hilde collection", labels)
        self.assertIn("Production: Rembrandt", labels)
        self.assertIn("Rembrandt", labels)

        self.assertTrue(data["classified_as"][0]["id"].startswith(f"{base_uri}data/concept/"))
        self.assertTrue(data["made_of"][0]["id"].startswith(f"{base_uri}data/concept/"))
        self.assertTrue(data["current_location"]["id"].startswith(f"{base_uri}data/place/"))
        self.assertTrue(data["member_of"][0]["id"].startswith(f"{base_uri}data/set/"))
        self.assertTrue(data["produced_by"]["id"].startswith(f"{base_uri}data/event/"))

    def test_assign_entity_uris_preserves_external_equivalent(self):
        base_uri = "http://localhost:8000/"
        data = {
            "type": "HumanMadeObject",
            "classified_as": [
                {
                    "id": "http://vocab.getty.edu/aat/300037222",
                    "type": "Type",
                    "_label": "coins (money)",
                }
            ],
        }
        entities = {}

        assign_entity_uris(data, entities, base_uri)

        concept_uri = data["classified_as"][0]["id"]
        self.assertTrue(concept_uri.startswith(f"{base_uri}data/concept/"))
        self.assertEqual(
            entities[concept_uri]["equivalent"],
            "http://vocab.getty.edu/aat/300037222",
        )

    def test_build_entity_record_creates_concept_place_set_and_event_records(self):
        base_uri = "http://localhost:8000/"
        cases = [
            ("Type", "coins (money)", "concept"),
            ("Place", "Depot C", "place"),
            ("Set", "Huis van Hilde collection", "set"),
            ("Production", "Production: Rembrandt", "event"),
        ]

        for entity_type, label, slug in cases:
            with self.subTest(entity_type=entity_type):
                uri = entity_uri(entity_type, label, base_uri)
                record = build_entity_record(uri, entity_type, label)

                self.assertIn(f"/data/{slug}/", uri)
                self.assertEqual(record["id"], uri)
                self.assertEqual(record["type"], entity_type)
                self.assertEqual(record["_label"], label)
                self.assertEqual(record["identified_by"][0]["content"], label)


if __name__ == "__main__":
    unittest.main()
