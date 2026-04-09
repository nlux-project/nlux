#!/usr/bin/env python3
"""
Reset the nlux API database — drops and recreates all tables.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import engine, Base
from app.models import Record  # noqa: F401 — ensure model is registered

with engine.connect() as conn:
    # Drop FTS virtual table first (SQLite requires explicit drop)
    conn.execute(text("DROP TABLE IF EXISTS records_fts"))
    conn.commit()

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

# Recreate FTS5 table with fresh rowid sequence
from app.config import settings
if settings.database_url.startswith("sqlite"):
    with engine.connect() as conn:
        conn.execute(text(
            "CREATE VIRTUAL TABLE IF NOT EXISTS records_fts "
            "USING fts5(search_text, content='records', content_rowid='rowid')"
        ))
        conn.commit()

print("Database reset complete.")
