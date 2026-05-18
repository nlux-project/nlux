#!/usr/bin/env python3
"""
Load AI enrichment sidecar JSONL into existing NLUX API records.

The sidecar is merged as a Linked Art `referred_to_by` note classified as
"AI Research Analysis"; catalog fields from the original record are not changed.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "data-pipeline"))

from pipeline.process.ai_enrichment import load_sidecar, merge_ai_enrichment  # noqa: E402


def candidate_record_uris(record_id: str, api_base: str) -> list[str]:
    candidates = [record_id]
    if "/data/object/" in record_id:
        object_id = record_id.rstrip("/").split("/")[-1]
        candidates.append(f"{api_base.rstrip('/')}/data/object/{object_id}")
    return list(dict.fromkeys(candidates))


def rebuild_fts_if_needed() -> None:
    from sqlalchemy import text

    from app.config import settings
    from app.database import engine

    if settings.database_url.startswith("sqlite"):
        with engine.connect() as conn:
            conn.execute(text("INSERT INTO records_fts(records_fts) VALUES('rebuild')"))
            conn.commit()


def load_ai_enrichment(sidecar_path: Path, base_uri: str | None = None) -> tuple[int, int, int]:
    from app.config import settings
    from app.database import SessionLocal
    from app.models import Record
    from scripts.search_text import extract_search_text, text_value

    api_base = base_uri or settings.base_url or "http://localhost:8000"
    sidecars = load_sidecar(sidecar_path)
    db = SessionLocal()
    found = updated = missing = 0
    try:
        for record_id, sidecar in sidecars.items():
            record = None
            for uri in candidate_record_uris(record_id, api_base):
                record = db.query(Record).filter(Record.uri == uri).first()
                if record:
                    break
            if not record:
                missing += 1
                continue

            found += 1
            data = json.loads(record.data)
            merged = merge_ai_enrichment(data, sidecar, api_base)
            if merged == data:
                continue
            record.type = merged.get("type", record.type)
            record.label = text_value(merged.get("_label"))
            record.search_text = extract_search_text(merged)
            record.data = json.dumps(merged, ensure_ascii=False)
            updated += 1

        db.commit()
        if updated:
            rebuild_fts_if_needed()
    finally:
        db.close()
    return found, updated, missing


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load AI enrichment sidecar JSONL into the NLUX API database.")
    parser.add_argument("sidecar", help="AI enrichment JSONL file or directory")
    parser.add_argument("--base-uri", default=None, help="API base URI used for local concept ids and URI matching")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    found, updated, missing = load_ai_enrichment(Path(args.sidecar), args.base_uri)
    print(f"Done: {updated} updated, {found - updated} already enriched, {missing} missing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
