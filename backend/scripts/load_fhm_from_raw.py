#!/usr/bin/env python3
"""
Generate Linked Art records for the Frans Hals Museum (FHM) from raw
Adlib harvest files, using the data-pipeline's FhmMapper (includes image
representations and object-page links), then load them into the nlux
backend database.

The harvester captures deep-zoom (DZI) image descriptors; a DZI URL is
XML and cannot be rendered by the carousel. The FHM image proxy serves
plain jpegs for the same asset when the .dzi suffix is replaced with
.jpg (plus a &width= resize), which this loader applies to the mapped
records.

Only records with an image (image_dzi) and a real title (titles or
object_name) are selected. Record URIs are minted under the FHM objectid
namespace, which is also what the carousel's "fhm" collection filters
on.

Usage (from backend/ or repo root):
    python scripts/load_fhm_from_raw.py [--count 400] [--seed 42]
        [--input DIR] [--outdir DIR] [--reset] [--no-load]

Input dir defaults to $LUX_BASEPATH/data/input/fhm (flat directory of
per-record JSON files; see harvest-fhm.sh).
"""
import argparse
import importlib
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

FHM_NAMESPACE = "http://collectie.franshalsmuseum.nl/?query=search=objectid="

# Plain-image variant request width; the FHM image proxy resizes on request.
IMAGE_WIDTH = 1200


class _StubConfigs:
    """Minimal stand-in for pipeline Config, sufficient for FhmMapper."""

    internal_uri = os.getenv("NLUX_API", "http://localhost:8000") + "/data/"
    data_dir = "/tmp"
    globals = {}
    results = {"merged": {}}

    def get_idmap(self):
        return {}


def _clean(value) -> str:
    return str(value or "").strip()


def has_image_and_title(rec: dict) -> bool:
    """True if the raw Adlib record has an image and a real title."""
    if not _clean(rec.get("image_dzi")):
        return False
    titles = [_clean(t) for t in rec.get("titles", []) if _clean(t)]
    return bool(titles or _clean(rec.get("object_name")))


def dzi_to_jpeg(doc: dict) -> None:
    """Rewrite DZI (deep-zoom XML) access points to plain jpeg URLs."""
    for rep in doc.get("representation", []) or []:
        for digital in rep.get("digitally_shown_by", []) or []:
            for ap in digital.get("access_point", []) or []:
                if isinstance(ap, dict) and isinstance(ap.get("id"), str) \
                        and ap["id"].endswith(".dzi"):
                    ap["id"] = f"{ap['id'][:-4]}.jpg&width={IMAGE_WIDTH}"
                    digital["format"] = "image/jpeg"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=os.path.join(
        os.getenv("LUX_BASEPATH", "/Users/lux/data-pipeline"),
        "data", "input", "fhm"))
    parser.add_argument("--outdir", default=str(BACKEND_DIR / "sample_data" / "fhm_mapped"),
                        help="Directory to write mapped Linked Art JSON files")
    parser.add_argument("--count", type=int, default=400,
                        help="Number of records to map (default 400)")
    parser.add_argument("--seed", type=int, default=None,
                        help="Random seed for sampling")
    parser.add_argument("--reset", action="store_true",
                        help="Reset the backend database before loading")
    parser.add_argument("--no-load", action="store_true",
                        help="Only write files; skip database loading")
    args = parser.parse_args()

    model.factory.base_url = FHM_NAMESPACE

    input_dir = Path(args.input)
    if not input_dir.is_dir():
        print(f"Input directory not found: {input_dir}")
        sys.exit(1)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(args.seed)

    mapper_class = getattr(
        importlib.import_module("pipeline.sources.museums.fhm.mapper"),
        "FhmMapper")
    mapper = mapper_class({
        "namespace": FHM_NAMESPACE,
        "name": "fhm",
        "all_configs": _StubConfigs(),
    })

    all_files = list(input_dir.glob("*.json"))
    rng.shuffle(all_files)
    sample = []
    for path in all_files:
        if len(sample) >= args.count:
            break
        try:
            rec = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if has_image_and_title(rec):
            sample.append((path, rec))

    print(f"[fhm] selected {len(sample)} image+title records "
          f"from {len(all_files)} candidates")
    if not sample:
        print("No records selected")
        sys.exit(1)

    mapped = 0
    for path, rec in sample:
        result = mapper.transform({"data": rec})
        if not result or not result.get("data"):
            continue
        record_id = result.get("identifier") or path.stem
        dzi_to_jpeg(result["data"])
        out_path = outdir / f"fhm_{record_id}.json"
        out_path.write_text(
            json.dumps(result["data"], indent=2, ensure_ascii=False),
            encoding="utf-8")
        mapped += 1

    if not mapped:
        print("No records mapped")
        sys.exit(1)
    print(f"Mapped {mapped}/{len(sample)} records -> {outdir}")

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