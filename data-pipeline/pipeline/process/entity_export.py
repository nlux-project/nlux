from __future__ import annotations

import uuid
from typing import Any

CONTEXT = "https://linked.art/ns/v1/linked-art.json"
AAT_PREFERRED_NAME = "http://vocab.getty.edu/aat/300404670"
AAT_NAMED_COLLECTION = "http://vocab.getty.edu/aat/300456764"

AGENT_TYPES = {"Person", "Group", "Actor"}
PLACE_TYPES = {"Place"}
SET_TYPES = {"Set"}
CONCEPT_TYPES = {"Type", "Material", "Language", "MeasurementUnit", "Currency", "Concept"}
EVENT_TYPES = {"Activity", "Period", "Event", "Move", "Acquisition", "Production", "Encounter"}
EXPORTABLE_TYPES = AGENT_TYPES | PLACE_TYPES | SET_TYPES | CONCEPT_TYPES | EVENT_TYPES

KNOWN_GROUPS = {
    "Teylers Museum": "http://www.wikidata.org/entity/Q751582",
    "Frans Hals Museum": "http://www.wikidata.org/entity/Q574961",
    "Rijksmuseum Boerhaave": "http://www.wikidata.org/entity/Q759169",
    "Westfries Museum": "http://www.wikidata.org/entity/Q2382575",
}


def entity_slug(entity_type: str) -> str:
    if entity_type == "Person":
        return "person"
    if entity_type in {"Group", "Actor"}:
        return "group"
    if entity_type in PLACE_TYPES:
        return "place"
    if entity_type in SET_TYPES:
        return "set"
    if entity_type in CONCEPT_TYPES:
        return "concept"
    if entity_type in EVENT_TYPES:
        return "event"
    return entity_type.lower()


def entity_uri(entity_type: str, label: str, base_uri: str) -> str:
    base = base_uri.rstrip("/") + "/"
    slug = entity_slug(entity_type)
    uid = uuid.uuid5(uuid.NAMESPACE_DNS, f"{entity_type}:{label.strip().lower()}")
    return f"{base}data/{slug}/{uid}"


def agent_uri(agent_type: str, label: str, base_uri: str) -> str:
    base = base_uri.rstrip("/") + "/"
    slug = "person" if agent_type == "Person" else "group"
    uid = uuid.uuid5(uuid.NAMESPACE_DNS, label.strip().lower())
    return f"{base}data/{slug}/{uid}"


def _is_local_uri(uri: str, base_uri: str) -> bool:
    return uri.startswith(base_uri.rstrip("/") + "/")


def _name_from_identified_by(value: dict) -> str:
    if not isinstance(value, dict):
        return ""
    for identifier in value.get("identified_by", []) or []:
        if not isinstance(identifier, dict):
            continue
        content = identifier.get("content")
        if content:
            return content.strip()
    return ""


def _event_label(value: dict) -> str:
    label = (value.get("_label") or _name_from_identified_by(value)).strip()
    if label:
        return label

    pieces = []
    for agent in value.get("carried_out_by", []) or []:
        if not isinstance(agent, dict):
            continue
        agent_label = agent.get("_label") or _name_from_identified_by(agent)
        if agent_label:
            pieces.append(agent_label.strip())
    timespans = value.get("timespan") or []
    if isinstance(timespans, dict):
        timespans = [timespans]
    if isinstance(timespans, list):
        for timespan in timespans:
            timespan_label = _name_from_identified_by(timespan)
            if timespan_label:
                pieces.append(timespan_label)

    suffix = ": " + ", ".join(pieces) if pieces else ""
    return f"{value.get('type', 'Event')}{suffix}"


def _entity_label(value: dict) -> str:
    if value.get("type") in EVENT_TYPES:
        return _event_label(value)
    return (value.get("_label") or _name_from_identified_by(value)).strip()


def _compact_member_of(value: dict) -> None:
    member_of = value.get("member_of")
    if not member_of:
        return
    if isinstance(member_of, dict):
        member_of = [member_of]
    if not isinstance(member_of, list):
        return
    members = [
        member
        for member in member_of
        if not (
            isinstance(member, dict)
            and member.get("type") == "Set"
            and not member.get("id")
            and not _entity_label(member)
        )
    ]
    if members:
        value["member_of"] = members
    else:
        value.pop("member_of", None)


def _should_localize(entity_type: str, uri: str | None, base_uri: str) -> bool:
    if not uri:
        return True
    if _is_local_uri(uri, base_uri):
        return False
    if entity_type in CONCEPT_TYPES | PLACE_TYPES | SET_TYPES | EVENT_TYPES:
        return True
    return False


def assign_entity_uris(value: Any, entities: dict[str, dict], base_uri: str) -> None:
    if isinstance(value, dict):
        _compact_member_of(value)
        entity_type = value.get("type")
        if isinstance(entity_type, str) and entity_type in EXPORTABLE_TYPES:
            label = _entity_label(value)
            if label:
                original_uri = value.get("id")
                if entity_type == "Group" and label in KNOWN_GROUPS:
                    uri = KNOWN_GROUPS[label]
                elif entity_type in AGENT_TYPES and not original_uri:
                    uri = agent_uri(entity_type, label, base_uri)
                elif _should_localize(entity_type, original_uri, base_uri):
                    uri = entity_uri(entity_type, original_uri or label, base_uri)
                    if original_uri and original_uri != uri:
                        value["equivalent"] = [{"id": original_uri, "type": entity_type, "_label": label}]
                else:
                    uri = original_uri
                value["id"] = uri
                if uri not in entities:
                    info = {"type": entity_type, "label": label}
                    if original_uri and original_uri != uri:
                        info["equivalent"] = original_uri
                    entities[uri] = info
        for key, child in value.items():
            if key == "equivalent":
                continue
            assign_entity_uris(child, entities, base_uri)
    elif isinstance(value, list):
        for child in value:
            assign_entity_uris(child, entities, base_uri)


def assign_agent_uris(value: Any, agents: dict[str, dict], base_uri: str) -> None:
    assign_entity_uris(value, agents, base_uri)


def _identified_by(label: str) -> list[dict]:
    return [
        {
            "type": "Name",
            "content": label,
            "classified_as": [
                {
                    "id": AAT_PREFERRED_NAME,
                    "type": "Type",
                    "_label": "preferred name",
                }
            ],
        }
    ]


def _classifications(entity_type: str) -> list[dict]:
    if entity_type == "Set":
        return [
            {
                "type": "Type",
                "_label": "Named Collection",
                "equivalent": [
                    {
                        "id": AAT_NAMED_COLLECTION,
                        "type": "Type",
                        "_label": "named collections",
                    }
                ],
            }
        ]
    return []


def build_entity_record(uri: str, entity_type: str, label: str, equivalent: str | None = None) -> dict:
    record = {
        "@context": CONTEXT,
        "id": uri,
        "type": entity_type,
        "_label": label,
        "identified_by": _identified_by(label),
    }
    classifications = _classifications(entity_type)
    if classifications:
        record["classified_as"] = classifications
    if equivalent:
        record["equivalent"] = [{"id": equivalent, "type": entity_type, "_label": label}]
    return record


def build_agent_record(uri: str, agent_type: str, label: str) -> dict:
    return build_entity_record(uri, agent_type, label)
