from __future__ import annotations

import json
from typing import Optional, Tuple, List, Dict, Any
from sqlalchemy import text
from sqlalchemy.orm import Session
from .config import settings
from .models import Record

SCOPE_TYPES: Dict[str, List[str]] = {
    "item": ["HumanMadeObject", "DigitalObject"],
    "work": ["LinguisticObject", "VisualItem", "InformationObject"],
    "set": ["Set"],
    "agent": ["Person", "Group", "Actor"],
    "place": ["Place"],
    "concept": ["Type", "Material", "Language", "MeasurementUnit", "Currency", "Concept"],
    "event": ["Activity", "Period", "Event", "Move", "Acquisition"],
}


def _is_sqlite(db: Session) -> bool:
    return "sqlite" in settings.database_url


def _extract_query_text(q: str) -> str:
    """
    The frontend passes q as a JSON object e.g. {"text":"marcus"} or
    {"_scope":"item","text":"warhol"}. Extract the plain text value.
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
    page: int = 1,
    page_length: Optional[int] = None,
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Returns (items, total_count).
    items: list of Activity Streams stubs — [{"id": uri, "type": linked_art_type}, ...]
    page is 1-based.
    """
    q = _extract_query_text(q)
    if page_length is None:
        page_length = settings.page_length_default
    page_length = min(page_length, settings.page_length_max)
    offset = max(page - 1, 0) * page_length

    if _is_sqlite(db):
        return _sqlite_search(db, q, scope, offset, page_length)
    return _pg_search(db, q, scope, offset, page_length)


def count_records(db: Session, q: str, scope: str) -> int:
    """Return only the total count for a search query (used by search-estimate)."""
    q = _extract_query_text(q)
    _, total = search_records(db, q, scope, page=1, page_length=0)
    return total


def _type_placeholders(types: List[str]) -> Tuple[str, Dict]:
    params = {f"t{i}": t for i, t in enumerate(types)}
    clause = ", ".join(f":t{i}" for i in range(len(types)))
    return clause, params


def _sqlite_search(db: Session, q: str, scope: str, offset: int, limit: int):
    types = SCOPE_TYPES.get(scope, [])
    type_clause, type_params = _type_placeholders(types) if types else ("", {})

    try:
        if types:
            count_sql = text(
                f"SELECT COUNT(*) FROM records r "
                f"JOIN records_fts fts ON fts.rowid = r.rowid "
                f"WHERE records_fts MATCH :q AND r.type IN ({type_clause})"
            )
            total = db.execute(count_sql, {"q": q, **type_params}).scalar() or 0

            rows_sql = text(
                f"SELECT r.uri, r.type FROM records r "
                f"JOIN records_fts fts ON fts.rowid = r.rowid "
                f"WHERE records_fts MATCH :q AND r.type IN ({type_clause}) "
                f"LIMIT :limit OFFSET :offset"
            )
            rows = db.execute(rows_sql, {"q": q, **type_params, "limit": limit, "offset": offset}).fetchall()
        else:
            count_sql = text("SELECT COUNT(*) FROM records_fts WHERE records_fts MATCH :q")
            total = db.execute(count_sql, {"q": q}).scalar() or 0
            rows_sql = text(
                "SELECT r.uri, r.type FROM records r "
                "JOIN records_fts fts ON fts.rowid = r.rowid "
                "WHERE records_fts MATCH :q LIMIT :limit OFFSET :offset"
            )
            rows = db.execute(rows_sql, {"q": q, "limit": limit, "offset": offset}).fetchall()
    except Exception:
        # Fallback to LIKE if FTS table not yet populated
        like = f"%{q}%"
        query = db.query(Record).filter(Record.search_text.like(like))
        if types:
            query = query.filter(Record.type.in_(types))
        total = query.count()
        rows = [(r.uri, r.type) for r in query.offset(offset).limit(limit).all()]

    items = [{"id": row[0], "type": row[1]} for row in rows]
    return items, total


def _pg_search(db: Session, q: str, scope: str, offset: int, limit: int):
    types = SCOPE_TYPES.get(scope, [])
    type_clause, type_params = _type_placeholders(types) if types else ("", {})

    if types:
        sql_count = text(
            f"SELECT COUNT(*) FROM records "
            f"WHERE to_tsvector('simple', search_text) @@ plainto_tsquery('simple', :q) "
            f"AND type IN ({type_clause})"
        )
        total = db.execute(sql_count, {"q": q, **type_params}).scalar() or 0

        sql_rows = text(
            f"SELECT uri, type FROM records "
            f"WHERE to_tsvector('simple', search_text) @@ plainto_tsquery('simple', :q) "
            f"AND type IN ({type_clause}) "
            f"LIMIT :limit OFFSET :offset"
        )
        rows = db.execute(sql_rows, {"q": q, **type_params, "limit": limit, "offset": offset}).fetchall()
    else:
        sql_count = text(
            "SELECT COUNT(*) FROM records "
            "WHERE to_tsvector('simple', search_text) @@ plainto_tsquery('simple', :q)"
        )
        total = db.execute(sql_count, {"q": q}).scalar() or 0
        sql_rows = text(
            "SELECT uri, type FROM records "
            "WHERE to_tsvector('simple', search_text) @@ plainto_tsquery('simple', :q) "
            "LIMIT :limit OFFSET :offset"
        )
        rows = db.execute(sql_rows, {"q": q, "limit": limit, "offset": offset}).fetchall()

    items = [{"id": row[0], "type": row[1]} for row in rows]
    return items, total
