#!/usr/bin/env python3
"""Enrich harvested RBHC records by fetching full Adlib records by priref.

The Boerhaave `search=all` endpoint returns a reduced field set, even when
fields are requested explicitly. Re-fetching by priref adds mapper-critical
groups such as Description and Dimension.

Usage:
    uv run python enrich-rbhc.py [input_dir] [priref ...]
"""

import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

import warnings
warnings.filterwarnings("ignore", module="urllib3")


WEBAPI = "https://mmb-web.adlibhosting.com/ais6/webapi/wwwopac.ashx"
DATABASE = "collect"
ENRICH_FIELDS = {
    "Associated_person",
    "Associated_subject",
    "Description",
    "Dimension",
    "Inscription",
    "Material",
    "Technique",
}

input_dir = sys.argv[1] if len(sys.argv) > 1 else "data/input/rbhc"
only_prirefs = set(sys.argv[2:])
session = requests.Session()


def fetch_full(priref):
    url = f"{WEBAPI}?database={DATABASE}&search=priref={priref}&output=json"
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    records = data["adlibJSON"]["recordList"].get("record", [])
    return records[0] if records else None


def enrich_file(filepath):
    with open(filepath, encoding="utf-8") as fh:
        rec = json.load(fh)
    priref = str(rec.get("@priref", ""))
    if not priref:
        return priref, False, "no priref"

    if ENRICH_FIELDS.intersection(rec):
        return priref, False, "already enriched"

    try:
        full = fetch_full(priref)
    except Exception as exc:
        return priref, False, str(exc)

    if not full:
        return priref, False, "API returned no record"

    added = []
    for key in sorted(full.keys()):
        if key not in rec:
            rec[key] = full[key]
            added.append(key)

    if added:
        with open(filepath, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, ensure_ascii=False, indent=2)
        return priref, True, f"added: {', '.join(added)}"
    return priref, False, "no new fields"


files = sorted(
    os.path.join(input_dir, fn)
    for fn in os.listdir(input_dir)
    if fn.endswith(".json") and (not only_prirefs or fn.removesuffix(".json") in only_prirefs)
)
total = len(files)
print(f"RBHC: enriching {total} records from {input_dir} ...")

enriched = 0
skipped = 0
errors = 0
start = time.time()

with ThreadPoolExecutor(max_workers=10) as pool:
    futures = {pool.submit(enrich_file, fp): fp for fp in files}
    done = 0
    for future in as_completed(futures):
        done += 1
        priref, changed, msg = future.result()
        if changed:
            enriched += 1
        elif "error" in msg.lower() or "API returned" in msg:
            errors += 1
        else:
            skipped += 1
        if changed or total <= 20:
            print(f"  {priref}: {msg}")
        if done % 1000 == 0:
            elapsed = time.time() - start
            rate = done / elapsed if elapsed else 0
            print(f"  {done}/{total} ({rate:.0f}/s) - {enriched} enriched, {skipped} skipped, {errors} errors")

elapsed = time.time() - start
print(f"\nRBHC: done in {elapsed:.1f}s: {enriched} enriched, {skipped} skipped, {errors} errors")
