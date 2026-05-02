import json
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import _related_records
from app.models import Record
from app.search import search_records
from app.database import Base


PERSON_URI = "http://localhost:8000/data/person/jacobus-zaffius"
PLACE_URI = "http://localhost:8000/data/place/haarlem"


def _record(uri, linked_art_type, label, data):
    data = {"id": uri, "type": linked_art_type, "_label": label, **data}
    return Record(
        uri=uri,
        type=linked_art_type,
        label=label,
        search_text=json.dumps(data, ensure_ascii=False),
        data=json.dumps(data, ensure_ascii=False),
    )


class CrossCollectionGraphTest(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.db = Session()

        self.object_a = "http://localhost:8000/data/object/teylers-zaffius-object"
        self.object_b = "http://localhost:8000/data/object/frans-hals-zaffius-object"
        self.object_c = "http://localhost:8000/data/object/hvh-shared-place-object"

        self.db.add_all(
            [
                _record(
                    self.object_a,
                    "HumanMadeObject",
                    "Portrait of Jacobus Zaffius in the Teylers collection",
                    {
                        "member_of": [{"id": "http://localhost:8000/data/set/teylers", "type": "Set"}],
                        "produced_by": {
                            "type": "Production",
                            "carried_out_by": [{"id": PERSON_URI, "type": "Person", "_label": "Jacobus Zaffius"}],
                        },
                    },
                ),
                _record(
                    self.object_b,
                    "HumanMadeObject",
                    "Portrait of Jacobus Zaffius in the Frans Hals collection",
                    {
                        "member_of": [{"id": "http://localhost:8000/data/set/frans-hals-museum", "type": "Set"}],
                        "produced_by": {
                            "type": "Production",
                            "carried_out_by": [{"id": PERSON_URI, "type": "Person", "_label": "Jacobus Zaffius"}],
                            "took_place_at": [{"id": PLACE_URI, "type": "Place", "_label": "Haarlem"}],
                        },
                    },
                ),
                _record(
                    self.object_c,
                    "HumanMadeObject",
                    "Huis van Hilde object mentioning Haarlem",
                    {
                        "member_of": [{"id": "http://localhost:8000/data/set/huis-van-hilde", "type": "Set"}],
                        "current_location": {"id": PLACE_URI, "type": "Place", "_label": "Haarlem"},
                    },
                ),
                _record(
                    PERSON_URI,
                    "Person",
                    "Jacobus Zaffius",
                    {
                        "identified_by": [{"type": "Name", "content": "Jacobus Zaffius"}],
                        "born": {
                            "type": "Birth",
                            "timespan": {
                                "type": "TimeSpan",
                                "begin_of_the_begin": "1534-01-01T00:00:00",
                                "end_of_the_end": "1534-12-31T23:59:59",
                            },
                        },
                        "died": {
                            "type": "Death",
                            "timespan": {
                                "type": "TimeSpan",
                                "begin_of_the_begin": "1618-01-01T00:00:00",
                                "end_of_the_end": "1618-12-31T23:59:59",
                            },
                        },
                        "referred_to_by": [
                            {
                                "type": "LinguisticObject",
                                "content": "Jacobus Zaffius was a Catholic priest in Haarlem.",
                                "classified_as": [
                                    {
                                        "id": "http://localhost:8000/data/concept/display-biography",
                                        "type": "Type",
                                        "_label": "Display Biography",
                                    }
                                ],
                            }
                        ],
                    },
                ),
                _record(PLACE_URI, "Place", "Haarlem", {}),
            ]
        )
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_related_lists_traverse_cross_collection_person_place_chain(self):
        person_items, person_total = _related_records(
            self.db,
            scope="item",
            name="producedItem",
            uri=PERSON_URI,
            page=1,
            page_length=20,
        )

        self.assertEqual(person_total, 2)
        person_item_ids = {item["id"] for item in person_items}
        self.assertEqual(person_item_ids, {self.object_a, self.object_b})

        place_items, place_total = _related_records(
            self.db,
            scope="item",
            name="relatedToPlace",
            uri=PLACE_URI,
            page=1,
            page_length=20,
        )

        self.assertEqual(place_total, 2)
        place_item_ids = {item["id"] for item in place_items}
        self.assertEqual(place_item_ids, {self.object_b, self.object_c})

        self.assertIn(
            self.object_c,
            place_item_ids,
            "Object in collection C should be reachable through the place mentioned by collection B",
        )

    def test_structured_search_finds_cross_collection_shared_entities(self):
        person_query = json.dumps({"producedBy": {"id": PERSON_URI}})
        person_items, person_total = search_records(self.db, person_query, "item", page=1, page_length=20)

        self.assertEqual(person_total, 2)
        self.assertEqual({item["id"] for item in person_items}, {self.object_a, self.object_b})

        place_query = json.dumps({"encounteredBy": {"id": PLACE_URI}})
        place_items, place_total = search_records(self.db, place_query, "item", page=1, page_length=20)

        self.assertEqual(place_total, 1)
        self.assertEqual(place_items[0]["id"], self.object_b)

    def test_text_search_returns_zaffius_objects_person_and_haarlem_place(self):
        object_items, object_total = search_records(self.db, "Zaffius", "item", page=1, page_length=20)

        self.assertGreaterEqual(object_total, 2)
        object_ids = {item["id"] for item in object_items}
        self.assertIn(self.object_a, object_ids)
        self.assertIn(self.object_b, object_ids)

        agent_items, agent_total = search_records(self.db, "Zaffius", "agent", page=1, page_length=20)

        self.assertGreaterEqual(agent_total, 1)
        agent_ids = {item["id"] for item in agent_items}
        self.assertIn(PERSON_URI, agent_ids)

        person = self.db.query(Record).filter(Record.uri == PERSON_URI).one()
        person_data = json.loads(person.data)
        self.assertIn("born", person_data)
        self.assertIn("died", person_data)
        self.assertTrue(
            any(
                any(cls.get("_label") == "Display Biography" for cls in note.get("classified_as", []))
                for note in person_data.get("referred_to_by", [])
            ),
            "People & Groups result should include a biography note",
        )

        place_items, place_total = search_records(self.db, "Haarlem", "place", page=1, page_length=20)

        self.assertGreaterEqual(place_total, 1)
        self.assertIn(PLACE_URI, {item["id"] for item in place_items})


if __name__ == "__main__":
    unittest.main()
