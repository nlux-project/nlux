#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from pipeline.process.ai_enrichment import load_sidecar, merge_ai_enrichment


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge AI enrichment sidecar JSONL into exported Linked Art JSONL.")
    parser.add_argument("export_input", help="Export JSONL file or directory")
    parser.add_argument("sidecar", help="AI enrichment JSONL file or directory")
    parser.add_argument("--output-dir", default="data/output/latest-ai-enriched", help="Directory for merged JSONL files")
    parser.add_argument("--base-uri", default="https://nlux.local/", help="Base URI for local NLUX concept ids")
    return parser.parse_args()


def iter_export_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(path.glob("*.jsonl"))


def merge_file(input_path: Path, output_path: Path, sidecars: dict[str, dict], base_uri: str) -> tuple[int, int]:
    total = 0
    enriched = 0
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with input_path.open(encoding="utf-8") as src, output_path.open("w", encoding="utf-8") as dst:
        for line in src:
            if not line.strip():
                continue
            record = json.loads(line)
            record_id = record.get("id") or record.get("@id")
            if record_id in sidecars:
                before = len(record.get("referred_to_by", []))
                record = merge_ai_enrichment(record, sidecars[record_id], base_uri)
                after = len(record.get("referred_to_by", []))
                if after > before:
                    enriched += 1
            dst.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")))
            dst.write("\n")
            total += 1
    return total, enriched


def main() -> int:
    args = parse_args()
    export_input = Path(args.export_input)
    output_dir = Path(args.output_dir)
    sidecars = load_sidecar(Path(args.sidecar))

    total = 0
    enriched = 0
    for input_file in iter_export_files(export_input):
        file_total, file_enriched = merge_file(
            input_file,
            output_dir / input_file.name,
            sidecars,
            args.base_uri,
        )
        total += file_total
        enriched += file_enriched
        print(f"{input_file.name}: {file_enriched}/{file_total} records received AI enrichment")

    print(f"Done: {enriched}/{total} records received AI enrichment")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
