#!/usr/bin/env python3
"""
Scan all records in the nlux DB, extract unique Type/Material/Language/
MeasurementUnit/Currency/Concept references that have id URIs, and insert
stub records so the frontend can resolve them.

Usage:
    python scripts/generate_concepts.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.config import settings
from app.database import engine, SessionLocal
from app.models import Record

CONTEXT = "https://linked.art/ns/v1/linked-art.json"
CONCEPT_TYPES = {"Type", "Material", "Language", "MeasurementUnit", "Currency", "Concept"}


def _find_concepts(obj, concepts: dict):
    """Recursively find all concept-typed nodes with id URIs."""
    if isinstance(obj, dict):
        atype = obj.get("type")
        uri = obj.get("id")
        if atype in CONCEPT_TYPES and uri and uri.startswith("http"):
            label = obj.get("_label", atype)
            if uri not in concepts:
                concepts[uri] = {"type": atype, "label": label}
                # Preserve equivalent (original AAT URI)
                if "equivalent" in obj:
                    concepts[uri]["equivalent"] = obj["equivalent"]
        for v in obj.values():
            _find_concepts(v, concepts)
    elif isinstance(obj, list):
        for item in obj:
            _find_concepts(item, concepts)


def build_concept_record(uri: str, info: dict) -> dict:
    rec = {
        "@context": CONTEXT,
        "id": uri,
        "type": info["type"],
        "_label": info["label"],
        "identified_by": [{
            "type": "Name",
            "content": info["label"],
            "classified_as": [{
                "id": "http://vocab.getty.edu/aat/300404670",
                "type": "Type",
                "_label": "preferred name",
            }],
        }],
    }
    if "equivalent" in info:
        rec["equivalent"] = info["equivalent"]
    return rec


def run():
    db = SessionLocal()
    concepts: dict[str, dict] = {}

    print("Scanning records for concept references ...")
    total = db.query(Record).count()
    print(f"  {total} records to scan")

    n = 0
    for record in db.query(Record).yield_per(500):
        doc = json.loads(record.data)
        _find_concepts(doc, concepts)
        n += 1
        if n % 10000 == 0:
            print(f"  {n} scanned, {len(concepts)} concepts found so far ...")

    print(f"  {len(concepts)} unique concepts found")

    # Insert concept records (skip if already exists)
    inserted = 0
    for uri, info in concepts.items():
        if not db.query(Record).filter(Record.uri == uri).first():
            concept_doc = build_concept_record(uri, info)
            db.add(Record(
                uri=uri,
                type=info["type"],
                label=info["label"],
                search_text=info["label"],
                data=json.dumps(concept_doc, ensure_ascii=False),
            ))
            inserted += 1
    db.commit()
    print(f"  {inserted} concept records inserted")

    # Rebuild FTS index
    if settings.database_url.startswith("sqlite"):
        with engine.connect() as conn:
            conn.execute(text("INSERT INTO records_fts(records_fts) VALUES('rebuild')"))
            conn.commit()
        print("  FTS index rebuilt")

    db.close()
    print("Done.")


if __name__ == "__main__":
    run()
