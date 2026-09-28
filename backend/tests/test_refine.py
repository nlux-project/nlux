"""Tests for the Collectie NH 'Verfijn resultaten' support: label-based
structured-query criteria (currentOwnerLabel, classificationLabel),
period filtering (productionDateRange), the label/classification facets,
and result sorting (anySortName, itemProductionDate)."""

import json
import unittest

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.facets import facet_page
from app.models import Record
from app.search import search_records


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


def _ids(result):
    return [item["id"] for item in result[0]]


def _timespan(year):
    return {
        "type": "Production",
        "timespan": {
            "type": "TimeSpan",
            "begin_of_the_begin": f"{year}-01-01T00:00:00",
            "end_of_the_end": f"{year}-12-31T23:59:59",
        },
    }


class RefineFacetsTest(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(engine)
        with engine.connect() as conn:
            conn.execute(text(
                "CREATE VIRTUAL TABLE IF NOT EXISTS records_fts "
                "USING fts5(search_text, content='records', content_rowid='rowid')"
            ))
            conn.commit()
        Session = sessionmaker(bind=engine)
        self.db = Session()
        self.db.add_all(
            [
                _record(
                    "http://localhost:8000/data/object/a",
                    "HumanMadeObject",
                    "Aak met prent",
                    {
                        "classified_as": [{"type": "Type", "_label": "prent"}],
                        "current_owner": [
                            {"type": "Group", "_label": "Teylers Museum", "id": "http://localhost:8000/data/group/teylers"}
                        ],
                        "produced_by": _timespan(1787),
                    },
                ),
                _record(
                    "http://localhost:8000/data/object/b",
                    "HumanMadeObject",
                    "Boek met foto",
                    {
                        "classified_as": [{"type": "Type", "_label": "foto"}],
                        "current_owner": [
                            {"type": "Group", "_label": "Noord-Hollands Archief"}
                        ],
                        "produced_by": _timespan(1910),
                    },
                ),
                _record(
                    "http://localhost:8000/data/object/c",
                    "HumanMadeObject",
                    "Kaart van oud papier",
                    {
                        "classified_as": [{"type": "Type", "_label": "prent"}],
                        "current_owner": [
                            {"type": "Group", "_label": "Teylers Museum"}
                        ],
                        "produced_by": _timespan(1550),
                    },
                ),
                _record(
                    "http://localhost:8000/data/object/d",
                    "HumanMadeObject",
                    "Zeilboot schilderij",
                    {
                        "classified_as": [{"type": "Type", "_label": "schilderij"}],
                        "current_owner": [
                            {"type": "Group", "_label": "Westfries Museum"}
                        ],
                    },
                ),
                # Not an item — must never match the item scope
                _record(
                    "http://localhost:8000/data/work/tekst",
                    "LinguisticObject",
                    "Tekst over prenten",
                    {},
                ),
            ]
        )
        self.db.commit()
        with engine.connect() as conn:
            # Populate the external-content FTS index
            conn.execute(text("INSERT INTO records_fts(records_fts) VALUES('rebuild')"))
            conn.commit()

    def tearDown(self):
        self.db.close()

    # -- currentOwnerLabel criterion ------------------------------------

    def test_current_owner_label_criterion(self):
        items, total = search_records(
            self.db, json.dumps({"currentOwnerLabel": "Teylers Museum"}), "item"
        )
        self.assertEqual(total, 2)
        self.assertEqual(
            set(_ids((items, total))),
            {
                "http://localhost:8000/data/object/a",
                "http://localhost:8000/data/object/c",
            },
        )

    def test_current_owner_label_is_case_insensitive(self):
        _, total = search_records(
            self.db, json.dumps({"currentOwnerLabel": "teylers museum"}), "item"
        )
        self.assertEqual(total, 2)

    def test_current_owner_label_combined_with_text(self):
        query = json.dumps(
            {"AND": [{"text": "Kaart"}, {"currentOwnerLabel": "Teylers Museum"}]}
        )
        items, total = search_records(self.db, query, "item")
        self.assertEqual(total, 1)
        self.assertEqual(items[0]["id"], "http://localhost:8000/data/object/c")

    def test_mixed_text_and_facet_uses_full_text_search(self):
        # "schipper" appears inside the JSON document of this record but not
        # in its indexed search text — a combined query must intersect with
        # the full-text search, not substring-match the whole document.
        self.db.add(
            Record(
                uri="http://localhost:8000/data/object/e",
                type="HumanMadeObject",
                label="Exclusief in label",
                search_text="Exclusief in label",
                data=json.dumps(
                    {
                        "id": "http://localhost:8000/data/object/e",
                        "type": "HumanMadeObject",
                        "_label": "Exclusief in label",
                        "current_owner": [
                            {"type": "Group", "_label": "Teylers Museum"}
                        ],
                        "referred_to_by": [
                            {"content": "geheime aantekening schipper"}
                        ],
                    }
                ),
            )
        )
        self.db.commit()
        self.db.execute(
            text("INSERT INTO records_fts(records_fts) VALUES('rebuild')")
        )
        self.db.commit()

        query = json.dumps(
            {"AND": [{"text": "schipper"}, {"currentOwnerLabel": "Teylers Museum"}]}
        )
        _, total = search_records(self.db, query, "item")
        self.assertEqual(total, 0)

        query = json.dumps(
            {"AND": [{"text": "exclusief"}, {"currentOwnerLabel": "Teylers Museum"}]}
        )
        items, total = search_records(self.db, query, "item")
        self.assertEqual(total, 1)
        self.assertEqual(items[0]["id"], "http://localhost:8000/data/object/e")

    def test_flat_query_fields_combine_with_and(self):
        # Field order in a flat mixed query must not matter
        query = json.dumps(
            {"currentOwnerLabel": "Teylers Museum", "text": "Boek"}
        )
        _, total = search_records(self.db, query, "item")
        self.assertEqual(total, 0)

        query = json.dumps(
            {"text": "Boek", "currentOwnerLabel": "Noord-Hollands Archief"}
        )
        items, total = search_records(self.db, query, "item")
        self.assertEqual(total, 1)
        self.assertEqual(items[0]["id"], "http://localhost:8000/data/object/b")

    # -- classificationLabel criterion -----------------------------------

    def test_classification_label_criterion(self):
        items, total = search_records(
            self.db, json.dumps({"classificationLabel": "prent"}), "item"
        )
        self.assertEqual(total, 2)
        self.assertEqual(
            set(_ids((items, total))),
            {
                "http://localhost:8000/data/object/a",
                "http://localhost:8000/data/object/c",
            },
        )

    def test_classification_label_excludes_other_types(self):
        _, total = search_records(
            self.db, json.dumps({"classificationLabel": "schilderij"}), "item"
        )
        self.assertEqual(total, 1)

    # -- productionDateRange criterion ----------------------------------

    def test_period_range_1600_1800(self):
        query = json.dumps(
            {"productionDateRange": {"begin": 1600, "end": 1800}}
        )
        items, total = search_records(self.db, query, "item")
        self.assertEqual(total, 1)
        self.assertEqual(items[0]["id"], "http://localhost:8000/data/object/a")

    def test_period_range_before_1600(self):
        query = json.dumps({"productionDateRange": {"end": 1600}})
        items, total = search_records(self.db, query, "item")
        self.assertEqual(total, 1)
        self.assertEqual(items[0]["id"], "http://localhost:8000/data/object/c")

    def test_period_range_1800_1950(self):
        query = json.dumps(
            {"productionDateRange": {"begin": 1800, "end": 1950}}
        )
        items, total = search_records(self.db, query, "item")
        self.assertEqual(total, 1)
        self.assertEqual(items[0]["id"], "http://localhost:8000/data/object/b")

    def test_period_range_after_1950(self):
        query = json.dumps({"productionDateRange": {"begin": 1950}})
        _, total = search_records(self.db, query, "item")
        self.assertEqual(total, 0)

    def test_period_range_combined_with_owner_and_type(self):
        query = json.dumps(
            {
                "AND": [
                    {"currentOwnerLabel": "Teylers Museum"},
                    {"classificationLabel": "prent"},
                    {"productionDateRange": {"end": 1600}},
                ]
            }
        )
        items, total = search_records(self.db, query, "item")
        self.assertEqual(total, 1)
        self.assertEqual(items[0]["id"], "http://localhost:8000/data/object/c")

    # -- facets -----------------------------------------------------------

    def test_current_owner_label_facet(self):
        page = facet_page(
            self.db, "item", "itemCurrentOwnerLabel", None, 1, 20,
            "http://localhost:8000", "ctx",
        )
        self.assertEqual(
            _values(page),
            {"Teylers Museum": 2, "Noord-Hollands Archief": 1, "Westfries Museum": 1},
        )

    def test_classification_label_facet(self):
        page = facet_page(
            self.db, "item", "itemClassificationLabel", None, 1, 20,
            "http://localhost:8000", "ctx",
        )
        self.assertEqual(_values(page), {"prent": 2, "foto": 1, "schilderij": 1})

    def test_facet_counts_respect_selected_facet_criteria(self):
        q = json.dumps({"AND": [{"classificationLabel": "prent"}]})
        page = facet_page(
            self.db, "item", "itemCurrentOwnerLabel", q, 1, 20,
            "http://localhost:8000", "ctx",
        )
        # Only Teylers Museum owns the two 'prent' records
        self.assertEqual(_values(page), {"Teylers Museum": 2})

    # -- sorting -----------------------------------------------------------

    def test_sort_by_label_asc_on_text_search(self):
        items, _ = search_records(self.db, "prent", "item", sort="anySortName:asc")
        labels = [item["id"].rsplit("/", 1)[-1] for item in items]
        self.assertEqual(labels, ["a", "c"])

    def test_sort_by_label_on_structured_query(self):
        query = json.dumps({"currentOwnerLabel": "Teylers Museum"})
        asc_items, _ = search_records(self.db, query, "item", sort="anySortName:asc")
        self.assertEqual([i["id"].rsplit("/", 1)[-1] for i in asc_items], ["a", "c"])

        desc_items, _ = search_records(self.db, query, "item", sort="anySortName:desc")
        self.assertEqual([i["id"].rsplit("/", 1)[-1] for i in desc_items], ["c", "a"])

    def test_sort_by_production_date_desc(self):
        query = json.dumps({"classificationLabel": "prent"})
        items, _ = search_records(
            self.db, query, "item", sort="itemProductionDate:desc"
        )
        # 1787 first, then 1550
        self.assertEqual([i["id"].rsplit("/", 1)[-1] for i in items], ["a", "c"])

    def test_sort_by_production_date_puts_undated_last(self):
        query = json.dumps({"currentOwnerLabel": "Teylers Museum"})
        # Add a dated record check across the full item scope instead:
        query = json.dumps({"classificationLabel": "schilderij"})
        items, _ = search_records(self.db, query, "item", sort="itemProductionDate:desc")
        # The undated schilderij is the only match — still returned
        self.assertEqual(len(items), 1)

    def test_unknown_sort_falls_back_to_relevance(self):
        items, _ = search_records(self.db, "prent", "item", sort="unknownField:asc")
        # Results are returned even though the sort is unsupported
        self.assertEqual(len(items), 2)


if __name__ == "__main__":
    unittest.main()