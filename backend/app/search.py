from __future__ import annotations

import json
from typing import Optional, Tuple, List, Dict, Any
from sqlalchemy import text
from sqlalchemy.orm import Session
from .config import settings
from .models import Record


def _is_sqlite(db: Session) -> bool:
    return "sqlite" in settings.database_url


def _extract_query_text(q: str) -> str:
    """
    The frontend passes q as a JSON object e.g. {"text":"marcus"}.
    Extract the plain text value so it can be used in FTS queries.
    """
    try:
        parsed = json.loads(q)
        if isinstance(parsed, dict) and "text" in parsed:
            return parsed["text"]
    except (json.JSONDecodeError, TypeError):
        pass
    return q


def search_records(
    db: Session,
    q: str,
    scope: str,
    page: int = 0,
    page_length: Optional[int] = None,
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Returns (items, total_count).
    items: list of full JSON-LD dicts.
    """
    q = _extract_query_text(q)
    if page_length is None:
        page_length = settings.page_length_default
    page_length = min(page_length, settings.page_length_max)
    # Frontend uses 1-based page numbers; convert to 0-based offset
    offset = max(page - 1, 0) * page_length

    if _is_sqlite(db):
        return _sqlite_search(db, q, scope, offset, page_length)
    return _pg_search(db, q, scope, offset, page_length)


def _sqlite_search(db: Session, q: str, scope: str, offset: int, limit: int):
    # Use SQLite FTS5 virtual table if available, else LIKE fallback
    try:
        count_sql = text(
            "SELECT COUNT(*) FROM records_fts WHERE records_fts MATCH :q"
        )
        total = db.execute(count_sql, {"q": q}).scalar() or 0

        rows_sql = text(
            """
            SELECT r.data FROM records r
            JOIN records_fts fts ON fts.rowid = r.rowid
            WHERE records_fts MATCH :q
            LIMIT :limit OFFSET :offset
            """
        )
        rows = db.execute(rows_sql, {"q": q, "limit": limit, "offset": offset}).fetchall()
    except Exception:
        # Fallback to LIKE if FTS table not created yet
        like = f"%{q}%"
        total = db.query(Record).filter(Record.search_text.like(like)).count()
        rows = (
            db.query(Record.data)
            .filter(Record.search_text.like(like))
            .offset(offset)
            .limit(limit)
            .all()
        )

    items = [json.loads(row[0]) for row in rows]
    return items, total


def _pg_search(db: Session, q: str, scope: str, offset: int, limit: int):
    sql_count = text(
        "SELECT COUNT(*) FROM records WHERE to_tsvector('simple', search_text) @@ plainto_tsquery('simple', :q)"
    )
    total = db.execute(sql_count, {"q": q}).scalar() or 0

    sql_rows = text(
        """
        SELECT data FROM records
        WHERE to_tsvector('simple', search_text) @@ plainto_tsquery('simple', :q)
        LIMIT :limit OFFSET :offset
        """
    )
    rows = db.execute(sql_rows, {"q": q, "limit": limit, "offset": offset}).fetchall()
    items = [json.loads(row[0]) for row in rows]
    return items, total
