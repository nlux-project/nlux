import re
from collections.abc import Iterable

NHA_COLLECTION_SOURCE_HINTS = {
    "587 - portretten van de Provinciale Atlas Noord-Holland, Collectie van": "nha-c587",
    "480 - historieprenten van de Provinciale Atlas Noord-Holland, Collectie van": "nha-c480",
}


def export_filename(source_name: str, my_slice: int) -> str:
    safe_name = re.sub(r"[^A-Za-z0-9_-]+", "_", source_name).strip("_").lower()
    return f"export_{safe_name or 'shared'}_{my_slice}.jsonl"


def pop_source_filters(argv: list[str], source_names: Iterable[str]) -> set[str]:
    selected = set()
    for source_name in source_names:
        flag = f"--{source_name}"
        while flag in argv:
            argv.remove(flag)
            selected.add(source_name)
    return selected


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


def _source_names_from_member_of(data, internal_sources: set[str]) -> set[str]:
    source_names = set()
    if not isinstance(data, dict):
        return source_names
    member_of = data.get("member_of") or []
    if isinstance(member_of, dict):
        member_of = [member_of]
    for member in member_of:
        if not isinstance(member, dict):
            continue
        source_name = NHA_COLLECTION_SOURCE_HINTS.get(member.get("_label"))
        if source_name in internal_sources:
            source_names.add(source_name)
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
        source_names.update(_source_names_from_member_of(data, internal_sources))

    if not source_names:
        source_names.update(_source_names_from_equivalents(data, cfgs))

    return sorted(source_names) if source_names else ["shared"]


def filter_collection_sources(
    source_names: Iterable[str],
    selected_sources: set[str],
) -> list[str]:
    sources = list(source_names)
    if not selected_sources:
        return sources
    return [source_name for source_name in sources if source_name in selected_sources]
