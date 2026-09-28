#!/usr/bin/env python3
"""
Rebuild search_text (and the SQLite FTS index) from each record's Linked Art
data.

search_text is derived from the record JSON by the loader (extract_search_text
in scripts/load_data.py). When the derivation rules change — e.g. the
addition of current_owner / member_of labels so that records can be found by
the institution that holds them — existing databases keep the stale text
until they are fully reloaded. This script refreshes the column in place,
then rebuilds the FTS5 index for SQLite databases.

Usage (from backend/ or the repo root):
    python scripts/rebuild_search_text.py [--batch 2000]

Targets the database from DATABASE_URL (default: backend/nlux.db).
"""
import argparse
import json
import sys
from pathlib import Path

# Allow running from backend/ directory; load_data.py inserts backend/ itself
sys.path.insert(0, str(Path(__file__).parent))

from load_data import extract_search_text  # noqa: E402

from app.config import settings  # noqa: E402
from app.database import SessionLocal, engine  # noqa: E402
from app.models import Record  # noqa: E402


def rebuild(batch: int):
    db = SessionLocal()
    total = 0
    pending = 0
    try:
        for record in db.query(Record).yield_per(batch):
            try:
                doc = json.loads(record.data)
            except (TypeError, json.JSONDecodeError):
                continue
            new_text = extract_search_text(doc)
            if new_text != (record.search_text or ""):
                record.search_text = new_text
                total += 1
            pending += 1
            if pending >= batch:
                db.commit()
                print(f"  {total} records updated ...")
                pending = 0
        db.commit()
    finally:
        db.close()

    print(f"search_text rebuilt: {total} records updated")

    if settings.database_url.startswith("sqlite"):
        from sqlalchemy import text as sql_text

        with engine.connect() as conn:
            conn.execute(
                sql_text("INSERT INTO records_fts(records_fts) VALUES('rebuild')")
            )
            conn.commit()
        print("FTS index rebuilt")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--batch", type=int, default=2000, help="commit batch size (default 2000)"
    )
    args = parser.parse_args()
    rebuild(args.batch)