from __future__ import annotations

import uuid
from typing import Any

CONTEXT = "https://linked.art/ns/v1/linked-art.json"
AAT_PREFERRED_NAME = "http://vocab.getty.edu/aat/300404670"

KNOWN_GROUPS = {
    "Teylers Museum": "http://www.wikidata.org/entity/Q751582",
}


def agent_uri(agent_type: str, label: str, base_uri: str) -> str:
    base = base_uri.rstrip("/") + "/"
    slug = "person" if agent_type == "Person" else "group"
    uid = uuid.uuid5(uuid.NAMESPACE_DNS, label.strip().lower())
    return f"{base}data/{slug}/{uid}"


def assign_agent_uris(value: Any, agents: dict[str, dict], base_uri: str) -> None:
    if isinstance(value, dict):
        agent_type = value.get("type")
        if agent_type in {"Person", "Group"}:
            label = value.get("_label", "").strip()
            if label:
                if agent_type == "Group" and label in KNOWN_GROUPS:
                    uri = KNOWN_GROUPS[label]
                else:
                    uri = value.get("id") or agent_uri(agent_type, label, base_uri)
                value.setdefault("id", uri)
                agents.setdefault(uri, {"type": agent_type, "label": label})
        for child in value.values():
            assign_agent_uris(child, agents, base_uri)
    elif isinstance(value, list):
        for child in value:
            assign_agent_uris(child, agents, base_uri)


def build_agent_record(uri: str, agent_type: str, label: str) -> dict:
    return {
        "@context": CONTEXT,
        "id": uri,
        "type": agent_type,
        "_label": label,
        "identified_by": [
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
        ],
    }
