#!/usr/bin/env python3
"""
Enrich harvested Teylers records by re-fetching individually from the Adlib API.

The bulk search=all endpoint omits field groups like Dimension, Material,
Technique, and Content_subject. This script re-fetches each record by priref
to get the full field set, and merges the extra fields into the existing file.

Usage:
    uv run python enrich-teylers.py [input_dir]
"""
import sys
import os
import time
import json
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

WEBAPI = "https://teylers.adlibhosting.com/ais6/webapi/wwwopac.ashx"
ENRICH_FIELDS = {"Dimension", "Material", "Technique", "Content_subject",
                 "Description", "Inscription", "Label", "Object_category",
                 "Documentation", "credit_line", "dating.notes"}

input_dir = sys.argv[1] if len(sys.argv) > 1 else "data/input/teylers"
session = requests.Session()


def fetch_full(priref):
    url = f"{WEBAPI}?database=museum&search=priref={priref}&output=json"
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    records = data["adlibJSON"]["recordList"].get("record", [])
    return records[0] if records else None


def enrich_file(filepath):
    with open(filepath) as f:
        rec = json.load(f)
    priref = str(rec.get("@priref", ""))
    if not priref:
        return priref, False, "no priref"

    # Check if already enriched
    if any(field in rec for field in ENRICH_FIELDS):
        return priref, False, "already enriched"

    try:
        full = fetch_full(priref)
    except Exception as e:
        return priref, False, str(e)

    if not full:
        return priref, False, "API returned no record"

    # Merge new fields into existing record
    added = []
    for key in sorted(full.keys()):
        if key not in rec:
            rec[key] = full[key]
            added.append(key)

    if added:
        with open(filepath, "w") as f:
            json.dump(rec, f)
        return priref, True, f"added: {', '.join(added)}"
    return priref, False, "no new fields"


files = sorted(
    os.path.join(input_dir, fn)
    for fn in os.listdir(input_dir)
    if fn.endswith(".json")
)
total = len(files)
print(f"Enriching {total} records from {input_dir} ...")

enriched = 0
skipped = 0
errors = 0
start = time.time()

# Use thread pool for concurrent fetches (I/O bound)
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
        if done % 1000 == 0:
            elapsed = time.time() - start
            rate = done / elapsed if elapsed else 0
            print(f"  {done}/{total} ({rate:.0f}/s) — {enriched} enriched, {skipped} skipped, {errors} errors")

elapsed = time.time() - start
print(f"\nDone in {elapsed:.1f}s: {enriched} enriched, {skipped} skipped, {errors} errors")
