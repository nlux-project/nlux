#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from pipeline.process.ai_enrichment import (
    DEFAULT_MODEL,
    DEFAULT_PROMPT_VERSION,
    dry_run_response,
    error_sidecar_record,
    load_prompt_template,
    render_prompt,
    request_provider,
    sidecar_record,
)


def iter_export_records(input_path: Path, source: str | None):
    files = [input_path] if input_path.is_file() else sorted(input_path.glob("*.jsonl"))
    for file_path in files:
        if source and source not in file_path.stem:
            continue
        with file_path.open(encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    yield file_path, json.loads(line)


def existing_record_ids(output_path: Path) -> set[str]:
    if not output_path.exists():
        return set()
    ids = set()
    with output_path.open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("record_id"):
                ids.add(record["record_id"])
    return ids


def default_output_path(source: str, slice_num: int) -> Path:
    return Path("data/output/ai-enrichment") / f"{source}_{slice_num}.jsonl"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate NLUX AI enrichment sidecar JSONL from exported Linked Art records.")
    parser.add_argument("input", nargs="?", default="data/output/latest", help="Export JSONL file or directory")
    parser.add_argument("--source", default="all", help="Collection/source name used in output metadata")
    parser.add_argument("--slice", type=int, default=0, help="Slice number for default output naming")
    parser.add_argument("--max-slices", type=int, default=1, help="Total slices for deterministic record partitioning")
    parser.add_argument("--limit", type=int, default=0, help="Maximum records to process")
    parser.add_argument("--record-id", action="append", default=[], help="Only enrich a specific exported record id; repeatable")
    parser.add_argument("--output", help="Output sidecar JSONL path")
    parser.add_argument("--prompt", help="Prompt template path")
    parser.add_argument("--prompt-version", default=DEFAULT_PROMPT_VERSION)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--force", action="store_true", help="Write a new sidecar row even when output already contains the record")
    parser.add_argument("--dry-run", action="store_true", help="Render prompts and write skipped sidecar records without calling a provider")
    parser.add_argument("--progress-every", type=int, default=25, help="Print progress every N candidate records")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = args.source
    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else default_output_path(source, args.slice)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    template = load_prompt_template(args.prompt)
    wanted = set(args.record_id)
    done_ids = set() if args.force else existing_record_ids(output_path)

    processed = 0
    scanned = 0
    skipped_existing = 0
    skipped_filter = 0
    errors = 0
    print(
        f"AI enrichment: source={source}, slice={args.slice}/{args.max_slices}, "
        f"resume={'off' if args.force else 'on'}, existing_rows={len(done_ids)}"
    )
    with output_path.open("a", encoding="utf-8") as out:
        for index, (_, record) in enumerate(iter_export_records(input_path, None if source == "all" else source)):
            scanned += 1
            record_id = record.get("id") or record.get("@id")
            if not record_id:
                skipped_filter += 1
                continue
            if index % args.max_slices != args.slice:
                skipped_filter += 1
                continue
            if wanted and record_id not in wanted:
                skipped_filter += 1
                continue
            if record_id in done_ids:
                skipped_existing += 1
                continue

            try:
                prompt = render_prompt(record, template, args.prompt_version)
                if args.dry_run:
                    analysis = dry_run_response(record)
                    status = "skipped"
                else:
                    analysis = request_provider(prompt, args.model)
                    status = "ok"
                output = sidecar_record(record, source, args.model, args.prompt_version, analysis, status=status)
            except Exception as exc:
                output = error_sidecar_record(record, source, args.model, args.prompt_version, exc)
                errors += 1

            out.write(json.dumps(output, ensure_ascii=False, separators=(",", ":")))
            out.write("\n")
            processed += 1
            if args.progress_every and processed % args.progress_every == 0:
                print(
                    f"AI enrichment progress: wrote={processed}, scanned={scanned}, "
                    f"resumed_skips={skipped_existing}, filter_skips={skipped_filter}, errors={errors}",
                    flush=True,
                )
            if args.limit and processed >= args.limit:
                break

    print(
        f"Wrote {processed} AI enrichment sidecar rows to {output_path} "
        f"(scanned={scanned}, resumed_skips={skipped_existing}, filter_skips={skipped_filter}, errors={errors})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
