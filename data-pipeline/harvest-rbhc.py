#!/usr/bin/env python3
"""Harvest Rijksmuseum Boerhaave collection records from the Adlib WebAPI."""

import json
import sys
import time
from pathlib import Path

import requests

# suppress NotOpenSSLWarning: urllib3
import warnings
warnings.filterwarnings("ignore", module="urllib3")

WEBAPI = "https://mmb-web.adlibhosting.com/ais6/webapi/wwwopac.ashx"
DATABASE = "collect"
PAGE_SIZE = 100
FIELDS = (
    "priref,object_number,title,object_name,"
    "creator,creator.role,"
    "production.date.start,production.date.end,"
    "description,inscription.content,"
    "dimension,dimension.type,dimension.value,dimension.unit,"
    "material,technique,"
    "association.person,association.subject,"
    "location.default.name,"
    "reproduction.reference"
)


def fetch_page(startfrom):
    url = (
        f"{WEBAPI}?database={DATABASE}&search=all&output=json"
        f"&limit={PAGE_SIZE}&startfrom={startfrom}"
        f"&fields={FIELDS}"
    )
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return response.json()


def records_from_page(payload):
    try:
        return payload["adlibJSON"]["recordList"]["record"]
    except KeyError:
        return []


def total_hits(payload):
    try:
        return int(payload["adlibJSON"]["diagnostic"]["hits"])
    except (KeyError, TypeError, ValueError):
        return None


def main():
    out_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "data/input/rbhc")
    out_dir.mkdir(parents=True, exist_ok=True)

    startfrom = 1
    written = 0
    total = None

    while True:
        payload = fetch_page(startfrom)
        if total is None:
            total = total_hits(payload)
            if total:
                print(f"RBHC: harvesting {total} records into {out_dir}")

        records = records_from_page(payload)
        if not records:
            break

        for rec in records:
            priref = str(rec.get("@priref", ""))
            if not priref:
                continue
            with (out_dir / f"{priref}.json").open("w", encoding="utf-8") as fh:
                json.dump(rec, fh, ensure_ascii=False, indent=2)
            written += 1

        print(f"RBHC: wrote {written}/{total or '?'}")
        startfrom += PAGE_SIZE
        if total and startfrom > total:
            break
        time.sleep(0.1)

    print(f"RBHC: done, wrote {written} records")


if __name__ == "__main__":
    main()
