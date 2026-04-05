#!/usr/bin/env python3
"""
Extract Group references from Teylers Linked Art records and generate
stub Group JSON files in Linked Art format.

Usage:
    python scripts/generate_groups.py <input_dir> <output_dir>

Example:
    python scripts/generate_groups.py sample_data/teylers/objects/ sample_data/teylers/groups/
"""
import json
import re
import sys
from pathlib import Path


LINKED_ART_CONTEXT = "https://linked.art/ns/v1/linked-art.json"
BASE_URI = "https://teylers.adlibhosting.com/nlux/group/"


def slugify(name: str) -> str:
    slug = name.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug


def find_groups(obj, source_uri: str, groups: dict) -> None:
    if isinstance(obj, dict):
        if obj.get("type") == "Group":
            name = obj.get("_label", "").strip()
            if name:
                if name not in groups:
                    groups[name] = {"sources": []}
                if source_uri not in groups[name]["sources"]:
                    groups[name]["sources"].append(source_uri)
        for value in obj.values():
            find_groups(value, source_uri, groups)
    elif isinstance(obj, list):
        for item in obj:
            find_groups(item, source_uri, groups)


def build_group_record(name: str, sources: list) -> dict:
    slug = slugify(name)
    uri = BASE_URI + slug

    record = {
        "@context": LINKED_ART_CONTEXT,
        "id": uri,
        "type": "Group",
        "_label": name,
        "identified_by": [
            {
                "type": "Name",
                "content": name,
                "classified_as": [
                    {
                        "id": "http://vocab.getty.edu/aat/300404670",
                        "_label": "preferred name",
                    }
                ],
            }
        ],
    }

    if sources:
        record["referred_to_by"] = [
            {
                "type": "LinguisticObject",
                "content": f"Referenced in Teylers Museum record: {src_uri}",
                "classified_as": [
                    {
                        "id": "http://vocab.getty.edu/aat/300435416",
                        "_label": "source record",
                    }
                ],
                "subject_of": [
                    {
                        "type": "LinguisticObject",
                        "digitally_carried_by": [
                            {
                                "type": "DigitalObject",
                                "classified_as": [
                                    {
                                        "id": "http://vocab.getty.edu/aat/300264578",
                                        "_label": "web page",
                                    }
                                ],
                                "access_point": [{"id": src_uri}],
                                "format": "text/html",
                            }
                        ],
                    }
                ],
            }
            for src_uri in sources
        ]

    return record


def generate_groups(input_dir: Path, output_dir: Path) -> None:
    json_files = list(input_dir.glob("*.json"))
    if not json_files:
        print(f"No JSON files found in {input_dir}")
        sys.exit(1)

    groups: dict = {}

    for path in sorted(json_files):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
            source_uri = doc.get("id") or doc.get("@id") or path.name
            find_groups(doc, source_uri, groups)
        except Exception as e:
            print(f"  ERROR reading {path.name}: {e}")

    print(f"Found {len(groups)} unique Group references")

    output_dir.mkdir(parents=True, exist_ok=True)

    written = 0
    for name, data in groups.items():
        record = build_group_record(name, data["sources"])
        slug = slugify(name)
        out_path = output_dir / f"{slug}.json"
        out_path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  Wrote {out_path.name}  ({name})")
        written += 1

    print(f"Done: {written} group files written to {output_dir}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python scripts/generate_groups.py <input_dir> <output_dir>")
        sys.exit(1)
    generate_groups(Path(sys.argv[1]), Path(sys.argv[2]))
