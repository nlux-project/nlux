from __future__ import annotations

import json
import threading
from typing import Optional, Tuple, List, Dict, Any, Set
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
    "event": ["Activity", "Period", "Event", "Move", "Acquisition", "Production", "Encounter"],
}


def _is_sqlite(db: Session) -> bool:
    return "sqlite" in settings.database_url


def _parse_query(q: str) -> Any:
    try:
        return json.loads(q)
    except (json.JSONDecodeError, TypeError):
        return q


def _extract_query_text(q: str) -> str:
    """
    The frontend passes q as a JSON object e.g. {"text":"marcus"} or
    {"_scope":"item","text":"warhol"}. Extract the plain text value.
    """
    parsed = _parse_query(q)
    if isinstance(parsed, dict) and "text" in parsed:
        return parsed["text"]
    return q


def _walk_json(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_json(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_json(child)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _labels_at_paths(data: dict, paths: List[str]) -> list[str]:
    """Collect distinct _label strings at the given top-level paths."""
    labels: list[str] = []
    seen: set[str] = set()
    for path in paths:
        for node in _walk_json(data.get(path)):
            label = node.get("_label") if isinstance(node, dict) else None
            if isinstance(label, str) and label and label not in seen:
                seen.add(label)
                labels.append(label)
    return labels


def _has_label_at_paths(data: dict, paths: List[str], label: str) -> bool:
    wanted = label.strip().lower()
    return any(
        value.strip().lower() == wanted for value in _labels_at_paths(data, paths)
    )


_TIMESPAN_YEAR_KEYS = (
    "begin_of_the_begin",
    "begin_of_the_end",
    "end_of_the_begin",
    "end_of_the_end",
)


def _production_years(data: dict) -> list[int]:
    """Years appearing in produced_by timespans (used for period filtering)."""
    years: list[int] = []
    for produced_by in _as_list(data.get("produced_by")):
        if not isinstance(produced_by, dict):
            continue
        for timespan in _as_list(produced_by.get("timespan")):
            if not isinstance(timespan, dict):
                continue
            for key in _TIMESPAN_YEAR_KEYS:
                value = timespan.get(key)
                if isinstance(value, str) and value[:4].isdigit():
                    year = int(value[:4])
                    if year not in years:
                        years.append(year)
    return years


def _production_year_in_range(data: dict, value: Any) -> bool:
    """True when any production year falls in [begin, end) — begin inclusive, end exclusive."""
    if not isinstance(value, dict):
        return False
    begin = value.get("begin")
    end = value.get("end")
    try:
        begin_year = int(begin) if begin is not None else None
        end_year = int(end) if end is not None else None
    except (TypeError, ValueError):
        return False
    for year in _production_years(data):
        if (begin_year is None or year >= begin_year) and (
            end_year is None or year < end_year
        ):
            return True
    return False


def _has_nested_id(value: Any, uri: str) -> bool:
    return any(node.get("id") == uri for node in _walk_json(value))


def _text_matches(data: dict, text: str) -> bool:
    haystack = json.dumps(data, ensure_ascii=False).lower()
    return text.lower() in haystack


def _has_digital_image(data: dict) -> bool:
    for representation in data.get("representation", []) or []:
        if not isinstance(representation, dict):
            continue
        shown_by = representation.get("digitally_shown_by")
        shown_by = shown_by if isinstance(shown_by, list) else [shown_by]
        for digital in shown_by:
            if isinstance(digital, dict) and (
                digital.get("id") or digital.get("access_point")
            ):
                return True
    return False


FIELD_PATHS: Dict[str, List[str]] = {
    "producedBy": ["produced_by"],
    "encounteredBy": ["produced_by"],
    "productionInfluencedBy": ["produced_by"],
    "createdBy": ["created_by"],
    "publishedBy": ["created_by"],
    "creationInfluencedBy": ["created_by"],
    "carriedBy": ["carries", "digitally_carries"],
    "aboutAgent": ["about"],
    "classification": ["classified_as"],
    "material": ["made_of"],
    "memberOf": ["member_of", "part_of"],
}


def _criteria_id(criteria: Any) -> Optional[str]:
    if isinstance(criteria, dict):
        value = criteria.get("id")
        return value if isinstance(value, str) else None
    return None


# In-process cache of parsed Linked Art documents, so structured queries
# (e.g. hasDigitalImage) do not re-parse the full JSON of every record on
# every request. A hit is only reused while the raw document is unchanged,
# so reloading records stays correct.
_DOC_CACHE_MAX = 20_000
_doc_cache: Dict[str, Tuple[str, dict]] = {}
_doc_cache_lock = threading.Lock()


def _load_doc(record: Record) -> Optional[dict]:
    """Parse record.data with caching; None on invalid JSON."""
    raw = record.data
    with _doc_cache_lock:
        hit = _doc_cache.get(record.uri)
        if hit is not None and hit[0] == raw:
            return hit[1]
    try:
        doc = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None
    with _doc_cache_lock:
        if len(_doc_cache) >= _DOC_CACHE_MAX:
            _doc_cache.clear()
        _doc_cache[record.uri] = (raw, doc)
    return doc


# Structured-query results are cached per (scope, criteria) with a cheap
# database fingerprint (row count + total blob lengths for the scope).
# Any insert/update/delete changes the fingerprint, so reloading records
# invalidates the cache; unchanged fingerprints skip the full scan.
_json_result_cache: Dict[str, Tuple[Tuple, List[Tuple[str, str]]]] = {}
_json_result_lock = threading.Lock()


def _scope_fingerprint(db: Session, types: List[str]) -> Tuple:
    clause, params = _type_placeholders(types) if types else ("", {})
    where = f" WHERE type IN ({clause})" if types else ""
    sql = text(
        "SELECT COUNT(*), COALESCE(TOTAL(LENGTH(data)), 0), "
        "COALESCE(TOTAL(LENGTH(search_text)), 0) FROM records" + where)
    row = db.execute(sql, params).first()
    return tuple(row) if row else ()


def _matches_structured_query(
    data: dict, criteria: Any, text_uris: Optional[Dict[str, Set[str]]] = None
) -> bool:
    if not isinstance(criteria, dict):
        return False
    if "AND" in criteria:
        parts = criteria["AND"]
        return isinstance(parts, list) and all(
            _matches_structured_query(data, part, text_uris) for part in parts
        )
    if "OR" in criteria:
        parts = criteria["OR"]
        return isinstance(parts, list) and any(
            _matches_structured_query(data, part, text_uris) for part in parts
        )

    # A flat object is the AND of all of its fields.
    for field, value in criteria.items():
        if field in {"_lang", "_scope"}:
            continue
        if not _matches_single_criterion(data, field, value, text_uris):
            return False
    return True


def _matches_single_criterion(
    data: dict,
    field: str,
    value: Any,
    text_uris: Optional[Dict[str, Set[str]]] = None,
) -> bool:
    if field == "text":
        if not isinstance(value, str):
            return False
        if text_uris is not None:
            uris = text_uris.get(value.lower())
            return uris is not None and data.get("id") in uris
        return _text_matches(data, value)
    if field == "recordType":
        return data.get("type") == value
    if field == "hasDigitalImage":
        return _has_digital_image(data) == bool(value)
    if field == "currentOwnerLabel":
        return isinstance(value, str) and _has_label_at_paths(
            data, ["current_owner", "current_custodian"], value
        )
    if field == "classificationLabel":
        return isinstance(value, str) and _has_label_at_paths(
            data, ["classified_as"], value
        )
    if field == "productionDateRange":
        return _production_year_in_range(data, value)
    uri = _criteria_id(value)
    paths = FIELD_PATHS.get(field)
    if uri is None or paths is None:
        # Unknown field: ignore (treated as satisfied)
        return True
    return any(_has_nested_id(data.get(path), uri) for path in paths)


_STRUCTURED_QUERY_FIELDS = {
    "recordType",
    "hasDigitalImage",
    "currentOwnerLabel",
    "classificationLabel",
    "productionDateRange",
}


def _is_structured_query(parsed: Any) -> bool:
    if not isinstance(parsed, dict):
        return False
    if "AND" in parsed or "OR" in parsed:
        return True
    has_structured = any(
        key in FIELD_PATHS or key in _STRUCTURED_QUERY_FIELDS
        for key in parsed
        if key not in {"text", "_lang", "_scope"}
    )
    # A text-only query goes down the full-text search path
    return has_structured


SORT_FIELDS = {"anySortName", "itemProductionDate"}


def _parse_sort(sort: Optional[str]) -> Optional[Tuple[str, str]]:
    """Parse a 'field:direction' sort parameter into a supported pair."""
    if not sort:
        return None
    field, _, direction = sort.partition(":")
    if field not in SORT_FIELDS:
        return None
    if direction not in {"asc", "desc"}:
        direction = "asc" if field == "anySortName" else "desc"
    return field, direction


def _sort_key_for(field: str, label: str, data: dict) -> str:
    """Sort key for Python-side sorting of structured-query results."""
    if field == "itemProductionDate":
        years = _production_years(data)
        return str(min(years)) if years else ""
    return (label or "").lower()


def search_records(
    db: Session,
    q: str,
    scope: str,
    page: int = 1,
    page_length: Optional[int] = None,
    sort: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Returns (items, total_count).
    items: list of Activity Streams stubs — [{"id": uri, "type": linked_art_type}, ...]
    page is 1-based.
    """
    parsed = _parse_query(q)
    if page_length is None:
        page_length = settings.page_length_default
    page_length = min(page_length, settings.page_length_max)
    offset = max(page - 1, 0) * page_length
    parsed_sort = _parse_sort(sort)

    if _is_structured_query(parsed):
        return _json_search(
            db, parsed, scope, offset, page_length, parsed_sort
        )

    q = _extract_query_text(q)
    if _is_sqlite(db):
        return _sqlite_search(db, q, scope, offset, page_length, parsed_sort)
    return _pg_search(db, q, scope, offset, page_length, parsed_sort)


def count_records(db: Session, q: str, scope: str) -> int:
    """Return only the total count for a search query (used by search-estimate)."""
    q = _extract_query_text(q)
    _, total = search_records(db, q, scope, page=1, page_length=0)
    return total


def _type_placeholders(types: List[str]) -> Tuple[str, Dict]:
    params = {f"t{i}": t for i, t in enumerate(types)}
    clause = ", ".join(f":t{i}" for i in range(len(types)))
    return clause, params


def fts_match_expr(query_text: str) -> str:
    """
    Build an FTS5 MATCH expression from free text.

    Every whitespace-separated token is double-quoted so that punctuation
    inside a term (e.g. the hyphen in "Noord-Hollands") is not interpreted
    as an FTS5 query operator: an unquoted expression like that is parsed as
    a column filter and raises "no such column". Quoted tokens joined by a
    space keep the default implicit-AND semantics of multi-word searches.
    """
    tokens = [t for t in query_text.split() if t]
    if not tokens:
        return '""'
    return " ".join('"' + t.replace('"', '""') + '"' for t in tokens)


def _collect_text_terms(node: Any, acc: List[str]) -> None:
    """Recursively collect all "text" terms from a structured query tree."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "text" and isinstance(value, str):
                acc.append(value)
            elif key in {"AND", "OR"} and isinstance(value, list):
                for part in value:
                    _collect_text_terms(part, acc)
    elif isinstance(node, list):
        for part in node:
            _collect_text_terms(part, acc)


def _fts_uris_for_text(db: Session, q: str) -> Set[str]:
    """
    URIs whose full-text index matches the given text query.
    Falls back to a LIKE query over search_text when FTS is unavailable.
    """
    try:
        rows = db.execute(
            text(
                "SELECT r.uri FROM records r "
                "JOIN records_fts fts ON fts.rowid = r.rowid "
                "WHERE records_fts MATCH :q"
            ),
            {"q": fts_match_expr(q)},
        ).fetchall()
    except Exception:
        rows = (
            db.query(Record.uri)
            .filter(Record.search_text.like(f"%{q}%"))
            .all()
        )
    return {row[0] for row in rows}


def _text_uri_sets(
    db: Session, criteria: dict
) -> Optional[Dict[str, Set[str]]]:
    """
    Precompute the FTS result set for every text term in the query tree so
    that mixed text/facet queries intersect with the exact full-text search
    instead of using substring matching over the document.
    """
    terms: List[str] = []
    _collect_text_terms(criteria, terms)
    if not terms:
        return None
    return {
        term.lower(): _fts_uris_for_text(db, term) for term in terms
    }


def _json_search(
    db: Session,
    criteria: dict,
    scope: str,
    offset: int,
    limit: int,
    parsed_sort: Optional[Tuple[str, str]] = None,
):
    types = SCOPE_TYPES.get(scope, [])

    sort_key_part = json.dumps(parsed_sort) if parsed_sort is not None else ""
    key = f"{scope}|{json.dumps(criteria, sort_keys=True, default=str)}|{sort_key_part}"
    fingerprint = _scope_fingerprint(db, types)
    with _json_result_lock:
        hit = _json_result_cache.get(key)
        if hit is not None and hit[0] == fingerprint:
            matches = hit[1]
        else:
            matches = None

    if matches is None:
        text_uris = _text_uri_sets(db, criteria)
        query = db.query(Record)
        if types:
            query = query.filter(Record.type.in_(types))

        matches = []
        for record in query.all():
            data = _load_doc(record)
            if data is None:
                continue
            if _matches_structured_query(data, criteria, text_uris):
                label = record.label or ""
                sort_value = (
                    _sort_key_for(parsed_sort[0], label, data)
                    if parsed_sort is not None
                    else ""
                )
                matches.append((record.uri, record.type, label, sort_value))

        if parsed_sort is not None:
            matches.sort(key=lambda match: match[3], reverse=(parsed_sort[1] == "desc"))

        matches = [
            (uri, linked_art_type, label)
            for uri, linked_art_type, label, _ in matches
        ]

        with _json_result_lock:
            if len(_json_result_cache) >= 256:
                _json_result_cache.pop(next(iter(_json_result_cache)))
            _json_result_cache[key] = (fingerprint, matches)

    total = len(matches)
    rows = matches[offset : offset + limit] if limit > 0 else []
    return [
        {"id": uri, "type": linked_art_type, "label": label}
        for uri, linked_art_type, label in rows
    ], total


def _sqlite_order_clause(parsed_sort: Optional[Tuple[str, str]]) -> str:
    """ORDER BY clause for the SQLite FTS path; empty when sorting by relevance."""
    if parsed_sort is None:
        return ""
    field, direction = parsed_sort
    if field == "itemProductionDate":
        date_expr = "json_extract(r.data, '$.produced_by.timespan.end_of_the_end')"
        # NULLS LAST in both directions, then by label for determinism
        return (
            f" ORDER BY ({date_expr} IS NULL), {date_expr} {direction}, "
            f"r.label COLLATE NOCASE"
        )
    return f" ORDER BY r.label COLLATE NOCASE {direction}"


def _sqlite_search(
    db: Session,
    q: str,
    scope: str,
    offset: int,
    limit: int,
    parsed_sort: Optional[Tuple[str, str]] = None,
):
    types = SCOPE_TYPES.get(scope, [])
    type_clause, type_params = _type_placeholders(types) if types else ("", {})
    order_clause = _sqlite_order_clause(parsed_sort)
    # Quote tokens so punctuation (e.g. hyphens in "Noord-Hollands") is not
    # parsed as an FTS5 column filter; unquoted it raises "no such column"
    # and the query silently degrades to the LIKE fallback.
    match_expr = fts_match_expr(q)

    try:
        if types:
            count_sql = text(
                f"SELECT COUNT(*) FROM records r "
                f"JOIN records_fts fts ON fts.rowid = r.rowid "
                f"WHERE records_fts MATCH :q AND r.type IN ({type_clause})"
            )
            total = db.execute(count_sql, {"q": match_expr, **type_params}).scalar() or 0

            rows_sql = text(
                f"SELECT r.uri, r.type, r.label FROM records r "
                f"JOIN records_fts fts ON fts.rowid = r.rowid "
                f"WHERE records_fts MATCH :q AND r.type IN ({type_clause}) "
                f"{order_clause} "
                f"LIMIT :limit OFFSET :offset"
            )
            rows = db.execute(rows_sql, {"q": match_expr, **type_params, "limit": limit, "offset": offset}).fetchall()
        else:
            count_sql = text("SELECT COUNT(*) FROM records_fts WHERE records_fts MATCH :q")
            total = db.execute(count_sql, {"q": match_expr}).scalar() or 0
            rows_sql = text(
                "SELECT r.uri, r.type, r.label FROM records r "
                "JOIN records_fts fts ON fts.rowid = r.rowid "
                f"WHERE records_fts MATCH :q {order_clause} "
                "LIMIT :limit OFFSET :offset"
            )
            rows = db.execute(rows_sql, {"q": match_expr, "limit": limit, "offset": offset}).fetchall()
    except Exception:
        # Fallback to LIKE if FTS table not yet populated
        like = f"%{q}%"
        query = db.query(Record).filter(Record.search_text.like(like))
        if types:
            query = query.filter(Record.type.in_(types))
        total = query.count()
        # The LIKE fallback cannot sort on the production date (stored in
        # JSON); fall back to label ordering whenever a sort is requested.
        if parsed_sort is not None:
            query = (
                query.order_by(Record.label.desc())
                if parsed_sort[1] == "desc"
                else query.order_by(Record.label)
            )
        rows = [(r.uri, r.type, r.label) for r in query.offset(offset).limit(limit).all()]

    items = [{"id": row[0], "type": row[1], "label": row[2]} for row in rows]
    return items, total


def _pg_order_clause(parsed_sort: Optional[Tuple[str, str]]) -> str:
    """ORDER BY clause for the PostgreSQL tsvector path; empty when sorting by relevance."""
    if parsed_sort is None:
        return ""
    field, direction = parsed_sort
    if field == "itemProductionDate":
        date_expr = "(data::jsonb #>> '{produced_by,timespan,end_of_the_end}')"
        return f" ORDER BY ({date_expr} IS NULL), {date_expr} {direction}, label"
    return f" ORDER BY lower(label) {direction}"


def _pg_search(
    db: Session,
    q: str,
    scope: str,
    offset: int,
    limit: int,
    parsed_sort: Optional[Tuple[str, str]] = None,
):
    types = SCOPE_TYPES.get(scope, [])
    type_clause, type_params = _type_placeholders(types) if types else ("", {})
    order_clause = _pg_order_clause(parsed_sort)

    if types:
        sql_count = text(
            f"SELECT COUNT(*) FROM records "
            f"WHERE to_tsvector('simple', search_text) @@ plainto_tsquery('simple', :q) "
            f"AND type IN ({type_clause})"
        )
        total = db.execute(sql_count, {"q": q, **type_params}).scalar() or 0

        sql_rows = text(
            f"SELECT uri, type, label FROM records "
            f"WHERE to_tsvector('simple', search_text) @@ plainto_tsquery('simple', :q) "
            f"AND type IN ({type_clause}) "
            f"{order_clause} "
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
            "SELECT uri, type, label FROM records "
            "WHERE to_tsvector('simple', search_text) @@ plainto_tsquery('simple', :q) "
            f"{order_clause} "
            "LIMIT :limit OFFSET :offset"
        )
        rows = db.execute(sql_rows, {"q": q, "limit": limit, "offset": offset}).fetchall()

    items = [{"id": row[0], "type": row[1], "label": row[2]} for row in rows]
    return items, total
