#!/usr/bin/env python3
"""
Generate Linked Art records for Teylers Museum from raw Adlib harvest files,
using the data-pipeline's TeylersMapper (includes image representations and
IIIF manifests), then load them into the nlux backend database.

Only records with a public web image (Media -> publish_on_web + reference
number) are selected, so every loaded object can be displayed.

Usage (from backend/ or repo root):
    python scripts/load_teylers_from_raw.py [--count 200] [--seed 42]
        [--input DIR] [--outdir DIR] [--reset] [--no-load]

Input dir defaults to $LUX_BASEPATH/data/input/teylers.
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

# cromulent must be configured BEFORE the mapper builds any records:
# URIs are minted as {base_url}{ClassName}/{ident}
from cromulent import model

BASE_URL = "https://teylers.adlibhosting.com/nlux/"

# The mapper references the API base for IIIF manifest URLs.
API_BASE = os.getenv("NLUX_API", "http://localhost:8000")


class _StubConfigs:
    """Minimal stand-in for pipeline Config, sufficient for TeylersMapper."""

    internal_uri = f"{API_BASE}/data/"
    data_dir = "/tmp"
    globals = {}
    results = {"merged": {}}

    def get_idmap(self):
        return {}


def has_public_image(rec: dict) -> bool:
    """True if the raw Adlib record has an image flagged publish_on_web."""
    for entry in rec.get("Media", []) or []:
        ref = entry.get("media.reference", {})
        publish = ref.get("publish_on_web", {})
        filename = ref.get("reference_number", {})
        publish_text = (publish or {}).get("spans", [{}])[0].get("text") if publish else None
        file_text = (filename or {}).get("spans", [{}])[0].get("text") if filename else None
        if publish_text and file_text:
            return True
    return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=os.path.join(
        os.getenv("LUX_BASEPATH", "/Users/lux/data-pipeline"),
        "data", "input", "teylers"))
    parser.add_argument("--outdir", default=str(BACKEND_DIR / "sample_data" / "teylers_mapped"),
                        help="Directory to write mapped Linked Art JSON files")
    parser.add_argument("--count", type=int, default=200,
                        help="Number of image-bearing records to map (default 200)")
    parser.add_argument("--seed", type=int, default=None,
                        help="Random seed for sampling")
    parser.add_argument("--reset", action="store_true",
                        help="Reset the backend database before loading")
    parser.add_argument("--no-load", action="store_true",
                        help="Only write files; skip database loading")
    args = parser.parse_args()

    model.factory.base_url = BASE_URL

    from pipeline.sources.museums.teylers.mapper import TeylersMapper

    input_dir = Path(args.input)
    if not input_dir.is_dir():
        print(f"Input directory not found: {input_dir}")
        sys.exit(1)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    # Sample raw records with public images.
    # Note: reading every file to check for images is far too slow for the
    # full harvest (~100k files), so sample filenames first and read only
    # enough candidates to satisfy --count.
    all_files = list(input_dir.glob("*.json"))
    if not all_files:
        print(f"No JSON files found in {input_dir}")
        sys.exit(1)

    rng = random.Random(args.seed)
    shuffled = all_files[:]
    rng.shuffle(shuffled)

    target = args.count if args.count else len(shuffled)
    sample = []
    for path in shuffled:
        if len(sample) >= target:
            break
        try:
            rec = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if has_public_image(rec):
            sample.append((path.name, rec))

    if not sample:
        print("No image-bearing records found in input directory")
        sys.exit(1)

    print(f"Selected {len(sample)} image-bearing records from {len(all_files)} "
          f"candidates in {input_dir}")

    mapper = TeylersMapper({
        "namespace": "teylers",
        "name": "teylers",
        "all_configs": _StubConfigs(),
    })

    mapped = skipped = 0
    for name, rec in sample:
        result = mapper.transform({"data": rec})
        if not result or not result.get("data"):
            print(f"  SKIP {name}: mapper returned no data")
            skipped += 1
            continue
        data = result["data"]
        priref = str(rec.get("@priref", ""))
        out_path = outdir / f"{priref}.json"
        out_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        mapped += 1

    print(f"Mapped {mapped} records -> {outdir} ({skipped} skipped)")

    if args.no_load:
        return

    # Load into backend DB (reuses the tested load_data loader)
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