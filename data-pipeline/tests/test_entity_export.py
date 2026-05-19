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
            "member_of": [{"type": "Set", "_label": "Huis van Hilde"}],
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
        self.assertIn("Huis van Hilde", labels)
        self.assertIn("Production: Rembrandt", labels)
        self.assertIn("Rembrandt", labels)

        self.assertTrue(data["classified_as"][0]["id"].startswith(f"{base_uri}data/concept/"))
        self.assertTrue(data["made_of"][0]["id"].startswith(f"{base_uri}data/concept/"))
        self.assertTrue(data["current_location"]["id"].startswith(f"{base_uri}data/place/"))
        self.assertTrue(data["member_of"][0]["id"].startswith(f"{base_uri}data/set/"))
        self.assertTrue(data["produced_by"]["id"].startswith(f"{base_uri}data/event/"))

    def test_assign_entity_uris_removes_blank_member_of_sets(self):
        base_uri = "http://localhost:8000/"
        data = {
            "type": "HumanMadeObject",
            "member_of": [
                {"type": "Set"},
                {"type": "Set"},
                {"type": "Set", "_label": "Rijksmuseum Amsterdam"},
            ],
        }
        entities = {}

        assign_entity_uris(data, entities, base_uri)

        self.assertEqual(len(data["member_of"]), 1)
        self.assertEqual(data["member_of"][0]["_label"], "Rijksmuseum Amsterdam")
        self.assertTrue(data["member_of"][0]["id"].startswith(f"{base_uri}data/set/"))

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

    def test_assign_entity_uris_uses_known_museum_group_authorities(self):
        base_uri = "http://localhost:8000/"
        data = {
            "type": "HumanMadeObject",
            "current_owner": [{"type": "Group", "_label": "Frans Hals Museum"}],
        }
        entities = {}

        assign_entity_uris(data, entities, base_uri)

        owner_uri = data["current_owner"][0]["id"]
        self.assertEqual(owner_uri, "http://www.wikidata.org/entity/Q574961")
        self.assertEqual(entities[owner_uri]["type"], "Group")
        self.assertEqual(entities[owner_uri]["label"], "Frans Hals Museum")

    def test_assign_entity_uris_skips_list_valued_type_nodes(self):
        base_uri = "http://localhost:8000/"
        data = {
            "type": "HumanMadeObject",
            "assigned_by": [
                {
                    "type": "AttributeAssignment",
                    "assigned": [
                        {
                            "id": "https://example.org/bibframe-instance",
                            "type": [
                                "http://id.loc.gov/ontologies/bibframe/Instance",
                                "LinguisticObject",
                            ],
                            "_label": "Unsupported nested reference",
                            "classified_as": [{"type": "Type", "_label": "Nested type"}],
                        }
                    ],
                }
            ],
        }
        entities = {}

        assign_entity_uris(data, entities, base_uri)

        self.assertEqual(
            data["assigned_by"][0]["assigned"][0]["id"],
            "https://example.org/bibframe-instance",
        )
        self.assertEqual(
            data["assigned_by"][0]["assigned"][0]["type"],
            ["http://id.loc.gov/ontologies/bibframe/Instance", "LinguisticObject"],
        )
        self.assertIn("Nested type", {info["label"] for info in entities.values()})

    def test_assign_entity_uris_accepts_list_valued_event_timespan(self):
        base_uri = "http://localhost:8000/"
        data = {
            "type": "HumanMadeObject",
            "produced_by": {
                "type": "Production",
                "carried_out_by": [{"type": "Person", "_label": "Maker"}],
                "timespan": [
                    {
                        "type": "TimeSpan",
                        "identified_by": [{"type": "Name", "content": "1900"}],
                    }
                ],
            },
        }
        entities = {}

        assign_entity_uris(data, entities, base_uri)

        labels = {info["label"] for info in entities.values()}
        self.assertIn("Production: Maker, 1900", labels)

    def test_build_entity_record_creates_concept_place_set_and_event_records(self):
        base_uri = "http://localhost:8000/"
        cases = [
            ("Type", "coins (money)", "concept"),
            ("Place", "Depot C", "place"),
            ("Set", "Huis van Hilde", "set"),
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

    def test_build_set_record_marks_it_as_named_collection(self):
        record = build_entity_record(
            "http://localhost:8000/data/set/example",
            "Set",
            "Huis van Hilde",
        )

        equivalents = [
            eq["id"]
            for classification in record["classified_as"]
            for eq in classification.get("equivalent", [])
        ]
        self.assertIn("http://vocab.getty.edu/aat/300456764", equivalents)

    def test_generated_person_record_preserves_embedded_life_dates(self):
        base_uri = "http://localhost:8000/"
        data = {
            "type": "HumanMadeObject",
            "produced_by": {
                "type": "Production",
                "carried_out_by": [
                    {
                        "type": "Person",
                        "_label": "Kittensteyn, Cornelis C. van",
                        "born": {
                            "type": "Birth",
                            "timespan": {
                                "type": "TimeSpan",
                                "begin_of_the_begin": "1598-01-01T00:00:00",
                                "end_of_the_end": "1598-12-31T23:59:59",
                            },
                        },
                        "died": {
                            "type": "Death",
                            "timespan": {
                                "type": "TimeSpan",
                                "begin_of_the_begin": "1652-01-01T00:00:00",
                                "end_of_the_end": "1652-12-31T23:59:59",
                            },
                        },
                    }
                ],
            },
        }
        entities = {}

        assign_entity_uris(data, entities, base_uri)
        person_uri = data["produced_by"]["carried_out_by"][0]["id"]
        person_info = entities[person_uri]
        person_record = build_entity_record(
            person_uri,
            person_info["type"],
            person_info["label"],
            person_info.get("equivalent"),
            person_info.get("details"),
        )

        self.assertEqual(person_record["_label"], "Kittensteyn, Cornelis C. van")
        self.assertEqual(
            person_record["born"]["timespan"]["begin_of_the_begin"],
            "1598-01-01T00:00:00",
        )
        self.assertEqual(
            person_record["died"]["timespan"]["end_of_the_end"],
            "1652-12-31T23:59:59",
        )


if __name__ == "__main__":
    unittest.main()
