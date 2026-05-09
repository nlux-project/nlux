import json
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.facets import facet_page
from app.models import Record
from app.search import search_records


TYPE_PAINTING = "http://vocab.getty.edu/aat/300033618"
TYPE_PRINT = "http://vocab.getty.edu/aat/300041273"
MATERIAL_PAPER = "http://vocab.getty.edu/aat/300014109"
COLLECTION_TEYLERS = "http://localhost:8000/data/set/teylers"
COLLECTION_NHA = "http://localhost:8000/data/set/nha"


def _record(uri, linked_art_type, label, data):
    data = {"id": uri, "type": linked_art_type, "_label": label, **data}
    return Record(
        uri=uri,
        type=linked_art_type,
        label=label,
        search_text=json.dumps(data, ensure_ascii=False),
        data=json.dumps(data, ensure_ascii=False),
    )


def _values(page):
    return {item["value"]: item["totalItems"] for item in page["orderedItems"]}


class FacetsTest(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.db = Session()
        self.db.add_all(
            [
                _record(
                    "http://localhost:8000/data/object/velsen-1",
                    "HumanMadeObject",
                    "Gezicht op Velsen",
                    {
                        "classified_as": [{"id": TYPE_PAINTING, "type": "Type"}],
                        "made_of": [{"id": MATERIAL_PAPER, "type": "Material"}],
                        "member_of": [{"id": COLLECTION_TEYLERS, "type": "Set"}],
                        "representation": [
                            {
                                "type": "VisualItem",
                                "digitally_shown_by": [
                                    {
                                        "type": "DigitalObject",
                                        "access_point": [{"id": "https://example.org/image.jpg"}],
                                    }
                                ],
                            }
                        ],
                    },
                ),
                _record(
                    "http://localhost:8000/data/object/velsen-2",
                    "HumanMadeObject",
                    "Prent van Velsen",
                    {
                        "classified_as": [{"id": TYPE_PRINT, "type": "Type"}],
                        "member_of": [{"id": COLLECTION_NHA, "type": "Set"}],
                    },
                ),
                _record(
                    "http://localhost:8000/data/object/haarlem-1",
                    "HumanMadeObject",
                    "Gezicht op Haarlem",
                    {
                        "classified_as": [{"id": TYPE_PAINTING, "type": "Type"}],
                        "member_of": [{"id": COLLECTION_TEYLERS, "type": "Set"}],
                    },
                ),
                _record(
                    "http://localhost:8000/data/work/velsen-text",
                    "LinguisticObject",
                    "Tekst over Velsen",
                    {},
                ),
            ]
        )
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_record_type_facet_counts_current_text_search(self):
        page = facet_page(
            self.db,
            "item",
            "itemRecordType",
            json.dumps({"text": "Velsen", "_lang": "en"}),
            1,
            20,
            "http://localhost:8000",
            "https://linked.art/ns/v1/search.json",
        )

        self.assertEqual(_values(page), {"HumanMadeObject": 2})
        self.assertEqual(page["partOf"]["totalItems"], 1)

    def test_type_material_collection_and_image_facets(self):
        q = json.dumps({"text": "Velsen", "_lang": "en"})

        type_page = facet_page(self.db, "item", "itemTypeId", q, 1, 20, "http://localhost:8000", "ctx")
        material_page = facet_page(self.db, "item", "itemMaterialId", q, 1, 20, "http://localhost:8000", "ctx")
        collection_page = facet_page(self.db, "item", "responsibleCollections", q, 1, 20, "http://localhost:8000", "ctx")
        image_page = facet_page(self.db, "item", "itemHasDigitalImage", q, 1, 20, "http://localhost:8000", "ctx")

        self.assertEqual(_values(type_page), {TYPE_PAINTING: 1, TYPE_PRINT: 1})
        self.assertEqual(_values(material_page), {MATERIAL_PAPER: 1})
        self.assertEqual(_values(collection_page), {COLLECTION_NHA: 1, COLLECTION_TEYLERS: 1})
        self.assertEqual(_values(image_page), {0: 1, 1: 1})

    def test_selected_facet_query_narrows_search_results(self):
        query = json.dumps(
            {
                "AND": [
                    {"text": "Velsen", "_lang": "en"},
                    {"classification": {"id": TYPE_PAINTING}},
                ]
            }
        )

        items, total = search_records(self.db, query, "item", page=1, page_length=20)

        self.assertEqual(total, 1)
        self.assertEqual(items[0]["id"], "http://localhost:8000/data/object/velsen-1")

    def test_unsupported_facet_returns_empty_page(self):
        page = facet_page(self.db, "item", "itemProductionDate", "Velsen", 1, 20, "http://localhost:8000", "ctx")

        self.assertEqual(page["orderedItems"], [])
        self.assertEqual(page["partOf"]["totalItems"], 0)


if __name__ == "__main__":
    unittest.main()
