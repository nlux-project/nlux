import re
from collections.abc import Iterable


def export_filename(source_name: str, my_slice: int) -> str:
    safe_name = re.sub(r"[^A-Za-z0-9_-]+", "_", source_name).strip("_").lower()
    return f"export_{safe_name or 'shared'}_{my_slice}.jsonl"


def _iter_equivalent_ids(data):
    if not isinstance(data, dict):
        return
    for equivalent in data.get("equivalent", []) or []:
        if isinstance(equivalent, dict) and equivalent.get("id"):
            yield equivalent["id"]


def _source_names_from_equivalents(data, cfgs) -> set[str]:
    source_names = set()
    for uri in _iter_equivalent_ids(data):
        try:
            split = cfgs.split_uri(uri)
        except Exception:
            split = None
        if split:
            source, _identifier = split
            if source.get("type") == "internal":
                source_names.add(source["name"])
    return source_names


def collection_sources_for_record(record: dict, data: dict, cfgs) -> list[str]:
    internal_sources = set(cfgs.internal.keys())
    source_names = set()

    sources = record.get("sources", []) or []
    if isinstance(sources, str):
        sources = [sources]
    if isinstance(sources, Iterable):
        source_names.update(src for src in sources if src in internal_sources)

    source = record.get("source")
    if source in internal_sources:
        source_names.add(source)

    if not source_names:
        source_names.update(_source_names_from_equivalents(data, cfgs))

    return sorted(source_names) if source_names else ["shared"]
