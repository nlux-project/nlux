#!/usr/bin/env python3
"""Harvest Frans Hals Museum collection records from CollectionConnection."""

import json
import sys
import time
from pathlib import Path

from pipeline.sources.museums.fhm.fetcher import FhmFetcher


class HarvestConfigs:
    allow_network = True


def main():
    out_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "data/input/fhm")
    out_dir.mkdir(parents=True, exist_ok=True)

    limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
    fetcher = FhmFetcher({"name": "fhm", "fetch": "", "all_configs": HarvestConfigs()})
    fetcher.enabled = True

    first = 1
    written = 0

    while True:
        try:
            record = fetcher.fetch_record_by_offset(first)
        except Exception as exc:
            print(f"FHM: failed to fetch offset {first}: {exc}")
            break

        objectid = str(record.get("objectid", ""))
        if not objectid:
            break

        with (out_dir / f"{objectid}.json").open("w", encoding="utf-8") as fh:
            json.dump(record, fh, ensure_ascii=False, indent=2)
        written += 1

        if written % 100 == 0:
            print(f"FHM: wrote {written} records")
        if limit and written >= limit:
            break

        first += 1
        time.sleep(0.05)

    print(f"FHM: done, wrote {written} records into {out_dir}")


if __name__ == "__main__":
    main()
