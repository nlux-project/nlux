from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from collections.abc import Iterator
from types import SimpleNamespace
from typing import Any, Callable, Union
from urllib.parse import quote

from sqlalchemy import text
from sqlalchemy.orm import Session

from .models import Record
from .search import (
    SCOPE_TYPES,
    _extract_query_text,
    _is_sqlite,
    _is_structured_query,
    _matches_structured_query,
    _parse_query,
    _type_placeholders,
)

FacetValue = Union[str, int]
FacetExtractor = Callable[[Record, dict[str, Any]], list[FacetValue]]
FACET_MATCH_LIMIT = 5000


@dataclass(frozen=True)
class FacetDefinition:
    scope: str
    extractor: FacetExtractor


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _walk_json(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_json(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_json(child)


def _ids_at_paths(data: dict[str, Any], paths: list[str]) -> list[str]:
    ids: list[str] = []
    seen: set[str] = set()
    for path in paths:
        for node in _walk_json(data.get(path)):
            value = node.get("id") if isinstance(node, dict) else None
            if isinstance(value, str) and value and value not in seen:
                seen.add(value)
                ids.append(value)
    return ids


def _values_at_path(value: Any, path: list[str]) -> list[Any]:
    values = [value]
    for key in path:
        next_values: list[Any] = []
        for item in values:
            if isinstance(item, dict):
                next_values.extend(_as_list(item.get(key)))
            elif isinstance(item, list):
                for child in item:
                    if isinstance(child, dict):
                        next_values.extend(_as_list(child.get(key)))
        values = next_values
    return values


def _ids_at_nested_paths(data: dict[str, Any], paths: list[list[str]]) -> list[str]:
    ids: list[str] = []
    seen: set[str] = set()
    for path in paths:
        for value in _values_at_path(data, path):
            for node in _walk_json(value):
                node_id = node.get("id") if isinstance(node, dict) else None
                if isinstance(node_id, str) and node_id and node_id not in seen:
                    seen.add(node_id)
                    ids.append(node_id)
    return ids


def _date_values_at_paths(data: dict[str, Any], paths: list[list[str]]) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    for path in paths:
        for timespan in _values_at_path(data, path):
            if not isinstance(timespan, dict):
                continue
            candidates = [
                timespan.get("begin_of_the_begin"),
                timespan.get("begin_of_the_end"),
                timespan.get("end_of_the_begin"),
                timespan.get("end_of_the_end"),
                timespan.get("_label"),
            ]
            for candidate in candidates:
                if isinstance(candidate, str) and candidate:
                    if candidate[:4].isdigit() and "-" not in candidate:
                        value = f"{candidate[:4]}-01-01T00:00:00"
                    else:
                        value = candidate
                    if value not in seen:
                        seen.add(value)
                        values.append(value)
                    break
    return values


def _record_type(record: Record, data: dict[str, Any]) -> list[str]:
    return [record.type] if record.type else []


def _has_digital_image(record: Record, data: dict[str, Any]) -> list[int]:
    for representation in _as_list(data.get("representation")):
        if not isinstance(representation, dict):
            continue
        for digital in _as_list(representation.get("digitally_shown_by")):
            if isinstance(digital, dict) and (
                digital.get("id") or digital.get("access_point")
            ):
                return [1]
    return [0]


def _classified_as(record: Record, data: dict[str, Any]) -> list[str]:
    return _ids_at_paths(data, ["classified_as"])


def _materials(record: Record, data: dict[str, Any]) -> list[str]:
    return _ids_at_paths(data, ["made_of"])


def _member_of(record: Record, data: dict[str, Any]) -> list[str]:
    return _ids_at_paths(data, ["member_of", "part_of"])


def _responsible_units(record: Record, data: dict[str, Any]) -> list[str]:
    return _ids_at_paths(data, ["current_owner", "current_custodian"])


def _production_agents(record: Record, data: dict[str, Any]) -> list[str]:
    return _ids_at_nested_paths(data, [["produced_by", "carried_out_by"]])


def _production_places(record: Record, data: dict[str, Any]) -> list[str]:
    return _ids_at_nested_paths(data, [["produced_by", "took_place_at"]])


def _production_techniques(record: Record, data: dict[str, Any]) -> list[str]:
    return _ids_at_nested_paths(data, [["produced_by", "technique"], ["used_for", "technique"]])


def _encountered_agents(record: Record, data: dict[str, Any]) -> list[str]:
    return _ids_at_nested_paths(data, [["encountered_by", "carried_out_by"]])


def _encountered_places(record: Record, data: dict[str, Any]) -> list[str]:
    return _ids_at_nested_paths(data, [["encountered_by", "took_place_at"]])


def _production_dates(record: Record, data: dict[str, Any]) -> list[str]:
    return _date_values_at_paths(data, [["produced_by", "timespan"]])


def _encountered_dates(record: Record, data: dict[str, Any]) -> list[str]:
    return _date_values_at_paths(data, [["encountered_by", "timespan"]])


FACETS: dict[str, FacetDefinition] = {
    "itemRecordType": FacetDefinition("item", _record_type),
    "workRecordType": FacetDefinition("work", _record_type),
    "conceptRecordType": FacetDefinition("concept", _record_type),
    "eventRecordType": FacetDefinition("event", _record_type),
    "itemHasDigitalImage": FacetDefinition("item", _has_digital_image),
    "itemIsOnline": FacetDefinition("item", _has_digital_image),
    "itemTypeId": FacetDefinition("item", _classified_as),
    "itemMaterialId": FacetDefinition("item", _materials),
    "itemProductionAgentId": FacetDefinition("item", _production_agents),
    "itemProductionPlaceId": FacetDefinition("item", _production_places),
    "itemProductionTechniqueId": FacetDefinition("item", _production_techniques),
    "itemProductionDate": FacetDefinition("item", _production_dates),
    "itemEncounteredAgentId": FacetDefinition("item", _encountered_agents),
    "itemEncounteredPlaceId": FacetDefinition("item", _encountered_places),
    "itemEncounteredDate": FacetDefinition("item", _encountered_dates),
    "responsibleCollections": FacetDefinition("item", _member_of),
    "responsibleUnits": FacetDefinition("item", _responsible_units),
}


def _text_matches(record: Record, text: str) -> bool:
    return text.lower() in (record.search_text or "").lower()


def _record_matches(record: Record, data: dict[str, Any], parsed_query: Any) -> bool:
    if isinstance(parsed_query, dict):
        if _is_structured_query(parsed_query):
            return _matches_structured_query(data, parsed_query)
        if isinstance(parsed_query.get("text"), str):
            return _text_matches(record, parsed_query["text"])
        return True
    if isinstance(parsed_query, str) and parsed_query:
        return _text_matches(record, parsed_query)
    return True


def _limited_scope_query(db: Session, scope: str):
    types = SCOPE_TYPES.get(scope, [])
    query = db.query(Record)
    if types:
        query = query.filter(Record.type.in_(types))
    return query.limit(FACET_MATCH_LIMIT)


def _text_query_records(db: Session, scope: str, query_text: str) -> Iterator[Record]:
    types = SCOPE_TYPES.get(scope, [])
    type_clause, type_params = _type_placeholders(types) if types else ("", {})
    if _is_sqlite(db):
        try:
            if types:
                sql = text(
                    f"SELECT r.uri, r.type, r.label, r.search_text, r.data FROM records r "
                    f"JOIN records_fts fts ON fts.rowid = r.rowid "
                    f"WHERE records_fts MATCH :q AND r.type IN ({type_clause}) "
                    f"LIMIT :limit"
                )
                rows = db.execute(
                    sql, {"q": query_text, **type_params, "limit": FACET_MATCH_LIMIT}
                ).fetchall()
            else:
                sql = text(
                    "SELECT r.uri, r.type, r.label, r.search_text, r.data FROM records r "
                    "JOIN records_fts fts ON fts.rowid = r.rowid "
                    "WHERE records_fts MATCH :q LIMIT :limit"
                )
                rows = db.execute(sql, {"q": query_text, "limit": FACET_MATCH_LIMIT}).fetchall()
            for row in rows:
                values = row._mapping
                yield SimpleNamespace(
                    uri=values["uri"],
                    type=values["type"],
                    label=values["label"],
                    search_text=values["search_text"],
                    data=values["data"],
                )
            return
        except Exception:
            pass

    if not _is_sqlite(db):
        try:
            if types:
                sql = text(
                    f"SELECT uri, type, label, search_text, data FROM records "
                    f"WHERE to_tsvector('simple', search_text) @@ plainto_tsquery('simple', :q) "
                    f"AND type IN ({type_clause}) LIMIT :limit"
                )
                rows = db.execute(
                    sql, {"q": query_text, **type_params, "limit": FACET_MATCH_LIMIT}
                ).fetchall()
            else:
                sql = text(
                    "SELECT uri, type, label, search_text, data FROM records "
                    "WHERE to_tsvector('simple', search_text) @@ plainto_tsquery('simple', :q) "
                    "LIMIT :limit"
                )
                rows = db.execute(sql, {"q": query_text, "limit": FACET_MATCH_LIMIT}).fetchall()
            for row in rows:
                values = row._mapping
                yield SimpleNamespace(
                    uri=values["uri"],
                    type=values["type"],
                    label=values["label"],
                    search_text=values["search_text"],
                    data=values["data"],
                )
            return
        except Exception:
            pass

    like = f"%{query_text}%"
    query = db.query(Record).filter(Record.search_text.like(like))
    if types:
        query = query.filter(Record.type.in_(types))
    yield from query.limit(FACET_MATCH_LIMIT).yield_per(500)


def matching_records(db: Session, q: str | None, scope: str) -> Iterator[tuple[Record, dict[str, Any]]]:
    parsed_query = _parse_query(q or "")
    query_text = _extract_query_text(q or "").strip()
    if query_text and (
        isinstance(parsed_query, str)
        or (isinstance(parsed_query, dict) and isinstance(parsed_query.get("text"), str))
    ):
        records = _text_query_records(db, scope, query_text)
    else:
        records = _limited_scope_query(db, scope).yield_per(500)

    for record in records:
        try:
            data = json.loads(record.data)
        except (TypeError, json.JSONDecodeError):
            continue
        if _record_matches(record, data, parsed_query):
            yield record, data


def facet_page(
    db: Session,
    scope: str,
    name: str,
    q: str | None,
    page: int,
    page_length: int,
    base_url: str,
    context_url: str,
    sort: str | None = None,
) -> dict[str, Any]:
    definition = FACETS.get(name)
    id_str = f"{base_url}/api/facets/{scope}?name={quote(name)}&q={quote(q or '')}&page={page}"
    if definition is None or definition.scope != scope:
        return {
            "@context": context_url,
            "id": id_str,
            "type": "OrderedCollectionPage",
            "orderedItems": [],
            "partOf": {"id": id_str, "type": "OrderedCollection", "totalItems": 0},
        }

    counts: Counter[FacetValue] = Counter()
    for record, data in matching_records(db, q, scope):
        counts.update(definition.extractor(record, data))

    if name.endswith("Date") and sort == "asc":
        values = sorted(counts.items(), key=lambda item: str(item[0]))
    else:
        values = sorted(counts.items(), key=lambda item: (-item[1], str(item[0])))
    total = len(values)
    offset = max(page - 1, 0) * page_length
    page_values = values[offset : offset + page_length]

    ordered_items = [
        {
            "id": f"{id_str}&value={quote(str(value))}",
            "type": "OrderedCollection",
            "value": value,
            "totalItems": count,
        }
        for value, count in page_values
    ]

    result: dict[str, Any] = {
        "@context": context_url,
        "id": id_str,
        "type": "OrderedCollectionPage",
        "orderedItems": ordered_items,
        "partOf": {
            "id": f"{base_url}/api/facets/{scope}?name={quote(name)}&q={quote(q or '')}",
            "type": "OrderedCollection",
            "totalItems": total,
        },
    }
    if offset + page_length < total:
        result["next"] = {
            "id": f"{base_url}/api/facets/{scope}?name={quote(name)}&q={quote(q or '')}&page={page + 1}",
            "type": "OrderedCollectionPage",
        }
    return result
