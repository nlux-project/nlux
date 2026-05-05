#!/usr/bin/env python3
"""Harvest Westfries Museum records from the Memorix mediabank API."""

import json
import sys
import time
from pathlib import Path

from pipeline.sources.museums.wfm.fetcher import WfmFetcher


class HarvestConfigs:
    allow_network = True


def main():
    out_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "data/input/wfm")
    out_dir.mkdir(parents=True, exist_ok=True)

    limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
    fetcher = WfmFetcher({"name": "wfm", "fetch": "", "all_configs": HarvestConfigs()})
    fetcher.enabled = True

    page = 1
    written = 0
    total_pages = None

    while True:
        try:
            payload = fetcher.fetch_page(page=page, rows=100)
        except Exception as exc:
            print(f"WFM: failed to fetch page {page}: {exc}")
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
                print(f"WFM: wrote {written} records")
            if limit and written >= limit:
                print(f"WFM: done, wrote {written} records into {out_dir}")
                return

        if total_pages and page >= int(total_pages):
            break
        page += 1
        time.sleep(0.05)

    print(f"WFM: done, wrote {written} records into {out_dir}")


if __name__ == "__main__":
    main()
