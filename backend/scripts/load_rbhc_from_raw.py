#!/usr/bin/env python3
"""
Generate Linked Art records for the Rijksmuseum Boerhaave (RBHC) from raw
Adlib harvest files, using the data-pipeline's RbhcMapper (includes image
representations and object-page links), then load them into the nlux
backend database.

Only records with an image reproduction (Reproduction -> reproduction
.reference) and a usable title (Title, else Object_name) are selected, so
every loaded object can be displayed. Record URIs are minted by the
mapper under the Boerhaave detail namespace
(https://mmb-web.adlibhosting.com/ais6/Details/collect/), which is also
what the carousel's "rbhc" collection filters on. The mapper also embeds
current_owner "Rijksmuseum Boerhaave" (so the institution's full-text
search finds the records) and the object page as detail link. Images are
Adlib getcontent URLs served from mmb-web.adlibhosting.com, already in the
backend's trusted image hosts.

The rbhc input directory is a flat directory of ~83k JSON files, which is
slow to enumerate completely on APFS, so the loader streams os.scandir()
lazily and stops early once enough qualifying candidates are collected;
it never lists the full directory.

Usage (from backend/ or repo root):
    python scripts/load_rbhc_from_raw.py [--count 400] [--seed 42]
        [--input DIR] [--outdir DIR] [--scan-cap 12000] [--reset] [--no-load]

Input dir defaults to $LUX_BASEPATH/data/input/rbhc (flat directory of
per-record JSON files; see harvest-rbhc.sh).
"""
import argparse
import json
import os
import random
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent
DATA_PIPELINE_DIR = REPO_ROOT / "data-pipeline"

# Make `pipeline.*` (data-pipeline) and `app.*` (backend) importable
sys.path.insert(0, str(DATA_PIPELINE_DIR))
sys.path.insert(0, str(BACKEND_DIR))

# cromulent must be configured BEFORE the mapper builds any records
from cromulent import model

# The mapper references the API base for IIIF manifest URLs.
API_BASE = os.getenv("NLUX_API", "http://localhost:8000")

RBHC_NAMESPACE = "https://mmb-web.adlibhosting.com/ais6/Details/collect/"


class _StubConfigs:
    """Minimal stand-in for pipeline Config, sufficient for RbhcMapper."""

    internal_uri = f"{API_BASE}/data/"
    data_dir = "/tmp"
    globals = {}
    results = {"merged": {}}

    def get_idmap(self):
        return {}


def has_image_and_title(rec: dict) -> bool:
    """True if the raw Adlib record has an image reference and a title."""
    from pipeline.sources.museums.rbhc.mapper import _group_values
    for entry in rec.get("Reproduction", []) or []:
        if _group_values([entry], "reproduction.reference"):
            break
    else:
        return False
    titles = list(_group_values(rec.get("Title", []), "title"))
    names = list(_group_values(rec.get("Object_name", []), "object_name"))
    return bool(titles or names)


def _scan_candidates(input_dir: Path, pool_target: int, scan_cap: int):
    """Stream scandir() lazily until pool_target qualifying records (or
    scan_cap files read); never a full listing of the flat 83k dir."""
    candidates, scanned = [], 0
    with os.scandir(input_dir) as entries:
        for entry in entries:
            if not entry.name.endswith(".json"):
                continue
            scanned += 1
            if scanned % 1000 == 0:
                print(f"[rbhc] scanned {scanned} files, "
                      f"{len(candidates)} candidates ...", flush=True)
            try:
                rec = json.loads(Path(entry.path).read_text(encoding="utf-8"))
            except Exception:
                continue
            if has_image_and_title(rec):
                candidates.append(rec)
            if len(candidates) >= pool_target or scanned >= scan_cap:
                break
    return candidates, scanned


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=os.path.join(
        os.getenv("LUX_BASEPATH", "/Users/lux/data-pipeline"),
        "data", "input", "rbhc"))
    parser.add_argument("--outdir", default=str(BACKEND_DIR / "sample_data" / "rbhc_mapped"),
                        help="Directory to write mapped Linked Art JSON files")
    parser.add_argument("--count", type=int, default=400,
                        help="Number of records to map (default 400)")
    parser.add_argument("--seed", type=int, default=None,
                        help="Random seed for sampling")
    parser.add_argument("--scan-cap", type=int, default=12000,
                        help="Max raw files to read while sampling candidates")
    parser.add_argument("--reset", action="store_true",
                        help="Reset the backend database before loading")
    parser.add_argument("--no-load", action="store_true",
                        help="Only write files; skip database loading")
    args = parser.parse_args()

    # Absolute URIs come from the mapper's namespace; keep cromulent's
    # factory base neutral so nothing gets double-prefixed.
    model.factory.base_url = RBHC_NAMESPACE

    input_dir = Path(args.input)
    if not input_dir.is_dir():
        print(f"Input directory not found: {input_dir}")
        sys.exit(1)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    pool_target = max(3 * args.count, 600)
    rng = random.Random(args.seed)
    candidates, scanned = _scan_candidates(input_dir, pool_target, args.scan_cap)
    print(f"[rbhc] scan done: {scanned} files read, {len(candidates)} candidates "
          f"(target {pool_target}; early exit, full dir not enumerated)", flush=True)
    if not candidates:
        print("No image+title records found in input directory")
        sys.exit(1)

    rng.shuffle(candidates)
    sample = candidates[:args.count]
    print(f"[rbhc] selected {len(sample)} image+title records "
          f"from {len(candidates)} candidates", flush=True)

    from pipeline.sources.museums.rbhc.mapper import RbhcMapper

    mapper = RbhcMapper({
        "namespace": RBHC_NAMESPACE,
        "name": "rbhc",
        "all_configs": _StubConfigs(),
    })

    mapped = skipped = 0
    for rec in sample:
        result = mapper.transform({"data": rec})
        if not result or not result.get("data"):
            skipped += 1
            continue
        priref = str(result.get("identifier") or rec.get("@priref", "unknown"))
        out_path = outdir / f"rbhc_{priref}.json"
        out_path.write_text(
            json.dumps(result["data"], indent=2, ensure_ascii=False),
            encoding="utf-8")
        mapped += 1
        if mapped % 50 == 0:
            print(f"[rbhc] {mapped}/{len(sample)} records mapped", flush=True)

    if not mapped:
        print("No records mapped")
        sys.exit(1)
    print(f"[rbhc] mapped {mapped} records -> {outdir} ({skipped} skipped)", flush=True)

    if args.no_load:
        return

    # Load into backend DB (reuses the tested load_data loader; upserts by URI)
    from scripts.load_data import load_path

    if args.reset:
        print("Resetting backend database ...")
        import subprocess
        subprocess.run(
            [sys.executable, str(BACKEND_DIR / "scripts" / "reset.py")],
            check=True)

    print(f"Loading {outdir} into backend database ...")
    load_path(outdir)


if __name__ == "__main__":
    main()