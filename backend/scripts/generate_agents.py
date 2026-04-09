#!/usr/bin/env python3
"""
Scan all records in the nlux DB, extract unique Person and Group references,
assign deterministic URIs, insert agent records, and update object records
so carried_out_by / current_owner nodes carry resolvable id fields.

Usage:
    python scripts/generate_agents.py
"""
import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.config import settings
from app.database import engine, SessionLocal
from app.models import Record

CONTEXT = "https://linked.art/ns/v1/linked-art.json"
AAT_PREFERRED_NAME = "http://vocab.getty.edu/aat/300404670"

# Known group URIs (use external authority when available)
KNOWN_GROUPS = {
    "Teylers Museum": "http://www.wikidata.org/entity/Q751582",
}


def _agent_uri(agent_type: str, label: str, base: str) -> str:
    slug = "person" if agent_type == "Person" else "group"
    uid = uuid.uuid5(uuid.NAMESPACE_DNS, label.strip().lower())
    return f"{base}data/{slug}/{uid}"


def _assign_uris(obj, agents: dict, base: str) -> bool:
    """Recursively find Person/Group nodes without ids, assign URIs.
    Returns True if any change was made."""
    changed = False
    if isinstance(obj, dict):
        atype = obj.get("type")
        if atype in ("Person", "Group") and "id" not in obj:
            label = obj.get("_label", "").strip()
            if label:
                if atype == "Group" and label in KNOWN_GROUPS:
                    uri = KNOWN_GROUPS[label]
                else:
                    uri = _agent_uri(atype, label, base)
                obj["id"] = uri
                agents.setdefault(uri, {"type": atype, "label": label})
                changed = True
        for v in obj.values():
            if _assign_uris(v, agents, base):
                changed = True
    elif isinstance(obj, list):
        for item in obj:
            if _assign_uris(item, agents, base):
                changed = True
    return changed


def build_agent_record(uri: str, atype: str, label: str) -> dict:
    return {
        "@context": CONTEXT,
        "id": uri,
        "type": atype,
        "_label": label,
        "identified_by": [{
            "type": "Name",
            "content": label,
            "classified_as": [{"id": AAT_PREFERRED_NAME, "type": "Type", "_label": "preferred name"}],
        }],
    }


def run():
    base = (settings.base_url.rstrip("/") + "/") if settings.base_url else "http://localhost:8000/"

    db = SessionLocal()
    agents: dict[str, dict] = {}

    print("Scanning records and assigning agent URIs ...")
    updated = 0
    batch = 0

    try:
        total = db.query(Record).count()
        print(f"  {total} records to scan")

        for record in db.query(Record).yield_per(500):
            doc = json.loads(record.data)
            changed = _assign_uris(doc, agents, base)
            if changed:
                raw = json.dumps(doc, ensure_ascii=False)
                record.data = raw
                updated += 1
                batch += 1
                if batch >= 1000:
                    db.commit()
                    print(f"  {updated} records updated so far ...")
                    batch = 0

        db.commit()
        print(f"  {updated} records updated, {len(agents)} unique agents found")

        # Insert agent records (skip if already exists)
        inserted = 0
        for uri, info in agents.items():
            if not db.query(Record).filter(Record.uri == uri).first():
                agent_doc = build_agent_record(uri, info["type"], info["label"])
                db.add(Record(
                    uri=uri,
                    type=info["type"],
                    label=info["label"],
                    search_text=info["label"],
                    data=json.dumps(agent_doc, ensure_ascii=False),
                ))
                inserted += 1
        db.commit()
        print(f"  {inserted} agent records inserted")

        # Rebuild FTS index
        if settings.database_url.startswith("sqlite"):
            with engine.connect() as conn:
                conn.execute(text("INSERT INTO records_fts(records_fts) VALUES('rebuild')"))
                conn.commit()
            print("  FTS index rebuilt")

    finally:
        db.close()

    print("Done.")


if __name__ == "__main__":
    run()
