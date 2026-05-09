from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from typing import Any, Callable, Union
from urllib.parse import quote

from sqlalchemy.orm import Session

from .models import Record
from .search import (
    SCOPE_TYPES,
    _is_structured_query,
    _matches_structured_query,
    _parse_query,
)

FacetValue = Union[str, int]
FacetExtractor = Callable[[Record, dict[str, Any]], list[FacetValue]]


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


FACETS: dict[str, FacetDefinition] = {
    "itemRecordType": FacetDefinition("item", _record_type),
    "workRecordType": FacetDefinition("work", _record_type),
    "conceptRecordType": FacetDefinition("concept", _record_type),
    "eventRecordType": FacetDefinition("event", _record_type),
    "itemHasDigitalImage": FacetDefinition("item", _has_digital_image),
    "itemTypeId": FacetDefinition("item", _classified_as),
    "itemMaterialId": FacetDefinition("item", _materials),
    "responsibleCollections": FacetDefinition("item", _member_of),
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


def matching_records(db: Session, q: str | None, scope: str) -> list[tuple[Record, dict[str, Any]]]:
    types = SCOPE_TYPES.get(scope, [])
    query = db.query(Record)
    if types:
        query = query.filter(Record.type.in_(types))

    parsed_query = _parse_query(q or "")
    matches: list[tuple[Record, dict[str, Any]]] = []
    for record in query.all():
        try:
            data = json.loads(record.data)
        except (TypeError, json.JSONDecodeError):
            continue
        if _record_matches(record, data, parsed_query):
            matches.append((record, data))
    return matches


def facet_page(
    db: Session,
    scope: str,
    name: str,
    q: str | None,
    page: int,
    page_length: int,
    base_url: str,
    context_url: str,
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
