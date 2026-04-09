#!/usr/bin/env python3
"""
Load Linked Art JSON files into the nlux-backend database.

Usage:
    python scripts/load_data.py <path/to/lux_metadata/>
"""
import json
import sys
from pathlib import Path

# Allow running from backend/ directory
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.config import settings
from app.database import engine, Base, SessionLocal
from app.models import Record


def extract_search_text(doc: dict) -> str:
    """Concatenate label and all referred_to_by content for FTS indexing."""
    parts = []
    if label := doc.get("_label"):
        parts.append(label)
    for item in doc.get("identified_by", []):
        if c := item.get("content"):
            parts.append(c)
    for item in doc.get("referred_to_by", []):
        if c := item.get("content"):
            parts.append(c)
    return " ".join(parts)


def load_directory(data_dir: Path):
    Base.metadata.create_all(bind=engine)

    # Ensure FTS5 table exists for SQLite
    if settings.database_url.startswith("sqlite"):
        with engine.connect() as conn:
            conn.execute(text(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS records_fts
                USING fts5(search_text, content='records', content_rowid='rowid')
                """
            ))
            conn.commit()

    json_files = sorted(data_dir.glob("*.json"))
    jsonl_files = sorted(data_dir.glob("*.jsonl"))
    if not json_files and not jsonl_files:
        print(f"No JSON files found in {data_dir}")
        sys.exit(1)

    # Rewrite pipeline placeholder URIs to match this API's base URL.
    # The pipeline uses internal_uri as a placeholder (e.g. https://your.local.domain/data/)
    # which must match DATA_API_BASE_URL in the lux-frontend config.
    api_base = (settings.base_url.rstrip("/") + "/") if settings.base_url else "http://localhost:8000/"
    _URI_REWRITES = [
        ("https://your.local.domain/data/", api_base + "data/"),
    ]

    def _rewrite_uris(raw: str) -> str:
        for old, new in _URI_REWRITES:
            if old in raw:
                raw = raw.replace(old, new)
        return raw

    db = SessionLocal()
    inserted = updated = errors = 0

    def _load_doc(doc: dict, source: str):
        nonlocal inserted, updated, errors
        # Pipeline output wraps Linked Art records in a datacache row;
        # unwrap if the record is a raw cache row rather than a Linked Art doc.
        if "data" in doc and isinstance(doc["data"], dict) and "id" not in doc:
            doc = doc["data"]
        # Rewrite placeholder base URIs before storing
        raw = _rewrite_uris(json.dumps(doc))
        doc = json.loads(raw)
        uri = doc.get("id") or doc.get("@id")
        if not uri:
            print(f"  SKIP {source} — no 'id' field")
            errors += 1
            return
        existing = db.query(Record).filter(Record.uri == uri).first()
        search_text = extract_search_text(doc)
        if existing:
            existing.type = doc.get("type", "")
            existing.label = doc.get("_label")
            existing.search_text = search_text
            existing.data = raw
            updated += 1
        else:
            db.add(Record(
                uri=uri,
                type=doc.get("type", ""),
                label=doc.get("_label"),
                search_text=search_text,
                data=raw,
            ))
            inserted += 1

    try:
        for path in json_files:
            try:
                doc = json.loads(path.read_text(encoding="utf-8"))
                _load_doc(doc, path.name)
            except Exception as e:
                print(f"  ERROR {path.name}: {e}")
                errors += 1

        for path in jsonl_files:
            print(f"Loading {path.name} ...")
            with path.open(encoding="utf-8") as fh:
                for lineno, line in enumerate(fh, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        doc = json.loads(line)
                        _load_doc(doc, f"{path.name}:{lineno}")
                    except Exception as e:
                        print(f"  ERROR {path.name}:{lineno}: {e}")
                        errors += 1
                    if (inserted + updated) % 1000 == 0 and (inserted + updated) > 0:
                        db.commit()
                        print(f"  {inserted} inserted, {updated} updated so far ...")

        db.commit()

        # Rebuild FTS index for SQLite
        if settings.database_url.startswith("sqlite"):
            with engine.connect() as conn:
                conn.execute(text("INSERT INTO records_fts(records_fts) VALUES('rebuild')"))
                conn.commit()

    finally:
        db.close()

    print(f"Done: {inserted} inserted, {updated} updated, {errors} errors")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/load_data.py <data_directory>")
        sys.exit(1)
    load_directory(Path(sys.argv[1]))
