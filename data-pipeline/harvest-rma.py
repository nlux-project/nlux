#!/usr/bin/env python3
"""Harvest Rijksmuseum Amsterdam Linked Art records."""

import json
import sys
import time
from pathlib import Path

from pipeline.sources.museums.rma.fetcher import RmaFetcher


class HarvestConfigs:
    allow_network = True


def main():
    args = sys.argv[1:]
    out_dir = Path(args[0] if args else "data/input/rma")
    out_dir.mkdir(parents=True, exist_ok=True)

    limit = int(args[1]) if len(args) > 1 else None
    fetcher = RmaFetcher({"name": "rma", "fetch": "", "all_configs": HarvestConfigs()})
    fetcher.enabled = True

    next_url = None
    written = 0

    while True:
        try:
            payload = fetcher.fetch_search_page(next_url)
        except Exception as exc:
            print(f"rma: failed to fetch search page: {exc}")
            break

        for item in payload.get("orderedItems", []) or []:
            identifier = fetcher.fix_identifier(item.get("id", ""))
            if not identifier:
                continue
            fetched = fetcher.fetch(identifier)
            if not fetched:
                continue
            with (out_dir / f"{identifier}.json").open("w", encoding="utf-8") as fh:
                json.dump(fetched["data"], fh, ensure_ascii=False, indent=2)
            written += 1
            if written % 100 == 0:
                print(f"rma: wrote {written} records")
            if limit and written >= limit:
                print(f"rma: done, wrote {written} records into {out_dir}")
                return
            time.sleep(0.02)

        next_url = (payload.get("next") or {}).get("id")
        if not next_url:
            break
        time.sleep(0.05)

    print(f"rma: done, wrote {written} records into {out_dir}")


if __name__ == "__main__":
    main()
