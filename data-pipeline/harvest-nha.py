#!/usr/bin/env python3
"""Harvest NHA records from the Memorix mediabank API."""

import json
import sys
import time
from pathlib import Path

# suppress NotOpenSSLWarning: urllib3
import warnings
warnings.filterwarnings("ignore", module="urllib3")

from pipeline.sources.museums.nha.c480.fetcher import NhaC480Fetcher
from pipeline.sources.museums.nha.c1477.fetcher import NhaC1477Fetcher
from pipeline.sources.museums.nha.c359.fetcher import NhaC359Fetcher
from pipeline.sources.museums.nha.c587.fetcher import NhaC587Fetcher


class HarvestConfigs:
    allow_network = True


SOURCES = {
    "nha-c1477": (NhaC1477Fetcher, "data/input/nha/c1477"),
    "nha-c359": (NhaC359Fetcher, "data/input/nha/c359"),
    "nha-c480": (NhaC480Fetcher, "data/input/nha/c480"),
    "nha-c587": (NhaC587Fetcher, "data/input/nha/c587"),
}


def _source_from_args(args):
    for arg in list(args):
        if arg.startswith("--source="):
            args.remove(arg)
            return arg.split("=", 1)[1]
        if arg in SOURCES:
            args.remove(arg)
            return arg
    if args:
        if "c1477" in args[0] or "1477" in args[0]:
            return "nha-c1477"
        if "c359" in args[0] or "359" in args[0]:
            return "nha-c359"
        if "c480" in args[0]:
            return "nha-c480"
    return "nha-c587"


def main():
    args = sys.argv[1:]
    source_name = _source_from_args(args)
    if source_name not in SOURCES:
        raise SystemExit(f"Unknown NHA source: {source_name}. Expected one of: {', '.join(sorted(SOURCES))}")

    fetcher_class, default_dir = SOURCES[source_name]
    out_dir = Path(args[0] if args else default_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    limit = int(args[1]) if len(args) > 1 else None
    fetcher = fetcher_class({"name": source_name, "fetch": "", "all_configs": HarvestConfigs()})
    fetcher.enabled = True

    page = 1
    written = 0
    total_pages = None

    while True:
        try:
            payload = fetcher.fetch_page(page=page, rows=100)
        except Exception as exc:
            print(f"{source_name}: failed to fetch page {page}: {exc}")
            break

        pagination = payload.get("metadata", {}).get("pagination", {})
        total_pages = total_pages or pagination.get("pages")
        records = payload.get("media") or []
        if not records:
            break

        for record in records:
            record_id = str(record.get("id", ""))
            if not record_id:
                continue
            with (out_dir / f"{record_id}.json").open("w", encoding="utf-8") as fh:
                json.dump(record, fh, ensure_ascii=False, indent=2)
            written += 1
            if written % 100 == 0:
                print(f"{source_name}: wrote {written} records")
            if limit and written >= limit:
                print(f"{source_name}: done, wrote {written} records into {out_dir}")
                return

        if total_pages and page >= int(total_pages):
            break
        page += 1
        time.sleep(0.05)

    print(f"{source_name}: done, wrote {written} records into {out_dir}")


if __name__ == "__main__":
    main()
