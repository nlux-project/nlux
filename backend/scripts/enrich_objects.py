#!/usr/bin/env python3
"""
Enrich Teylers object records by adding 'id' fields to inline Person and Place
references that only have '_label'. This allows the lux-frontend parsers to
render linked fields (author, publisher, place of publication, etc.).

URIs are derived from the same slugify logic used in generate_persons.py and
generate_places.py, so they will match the generated stub records.

Usage:
    python scripts/enrich_objects.py <input_dir> [--in-place]

    --in-place  overwrite the source files (default: print a diff summary)

Example:
    python scripts/enrich_objects.py sample_data/teylers/objects/ --in-place
"""
import json
import re
import sys
from pathlib import Path

BASE_URIS = {
    "Person": "https://teylers.adlibhosting.com/nlux/person/",
    "Actor":  "https://teylers.adlibhosting.com/nlux/person/",
    "Group":  "https://teylers.adlibhosting.com/nlux/group/",
    "Place":  "https://teylers.adlibhosting.com/nlux/place/",
}


def slugify(name: str) -> str:
    slug = name.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug


def enrich(obj):
    """Recursively add 'id' to inline Person/Place/Group nodes that lack one."""
    if isinstance(obj, dict):
        entity_type = obj.get("type")
        if entity_type in BASE_URIS and "id" not in obj and "_label" in obj:
            obj["id"] = BASE_URIS[entity_type] + slugify(obj["_label"])
        for value in obj.values():
            enrich(value)
    elif isinstance(obj, list):
        for item in obj:
            enrich(item)


def enrich_directory(input_dir: Path, in_place: bool) -> None:
    json_files = list(input_dir.glob("*.json"))
    if not json_files:
        print(f"No JSON files found in {input_dir}")
        sys.exit(1)

    enriched = 0
    for path in sorted(json_files):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
            original = json.dumps(doc)
            enrich(doc)
            updated = json.dumps(doc)
            if original != updated:
                enriched += 1
                if in_place:
                    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
                    print(f"  Enriched {path.name}")
                else:
                    print(f"  Would enrich {path.name} (run with --in-place to apply)")
        except Exception as e:
            print(f"  ERROR {path.name}: {e}")

    action = "enriched" if in_place else "would enrich"
    print(f"Done: {action} {enriched} of {len(json_files)} files")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/enrich_objects.py <input_dir> [--in-place]")
        sys.exit(1)
    in_place = "--in-place" in sys.argv
    enrich_directory(Path(sys.argv[1]), in_place)
