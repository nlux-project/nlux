#!/usr/bin/env python3
"""
Generate Linked Art records for the Noord-Hollands Archief (NHA) from raw
Memorix harvest files, using the data-pipeline's NhaMapper subclasses
(includes image representations and IIIF manifests), then load them into
the nlux backend database.

Only records with an image asset and a usable title (metadata beschrijving,
raw title or description) are selected, so every loaded object can be
displayed. Record URIs are minted under the shared NHA handle namespace
(https://hdl.handle.net/21.12102/), which is also what the carousel's
"nha" collection filters on.

Usage (from backend/ or repo root):
    python scripts/load_nha_from_raw.py [--count 400] [--seed 42]
        [--input DIR] [--outdir DIR] [--sources c480,c587] [--reset] [--no-load]

Input dir defaults to $LUX_BASEPATH/data/input/nha (subdirs c1477, c359,
c480, c587). --count is spread evenly over the selected sources.
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

NHA_NAMESPACE = "https://hdl.handle.net/21.12102/"

# The mapper references the API base for IIIF manifest URLs.
API_BASE = os.getenv("NLUX_API", "http://localhost:8000")

# source subdir -> (mapper class path, collection label)
SOURCES = {
    "c1477": ("pipeline.sources.museums.nha.c1477.mapper", "NhaC1477Mapper",
              "1477 - prenten van C.G. Voorhelm Schneevoogt te Haarlem"),
    "c359": ("pipeline.sources.museums.nha.c359.mapper", "NhaC359Mapper",
             "359 - prenten en tekeningen van de Provinciale Atlas Noord-Holland"),
    "c480": ("pipeline.sources.museums.nha.c480.mapper", "NhaC480Mapper",
             "480 - historieprenten van de Provinciale Atlas Noord-Holland"),
    "c587": ("pipeline.sources.museums.nha.c587.mapper", "NhaC587Mapper",
             "587 - portretten van de Provinciale Atlas Noord-Holland"),
}


class _StubConfigs:
    """Minimal stand-in for pipeline Config, sufficient for NhaMapper."""

    internal_uri = f"{API_BASE}/data/"
    data_dir = "/tmp"
    globals = {}
    results = {"merged": {}}

    def get_idmap(self):
        return {}


def has_image_and_title(rec: dict) -> bool:
    """True if the raw Memorix record has an image asset and a real title."""
    if not rec.get("asset"):
        return False
    for item in rec.get("metadata", []):
        if item.get("field") == "beschrijving":
            value = item.get("value")
            if isinstance(value, list):
                if any(str(v).strip() for v in value):
                    return True
            elif str(value or "").strip():
                return True
            break
    return bool((rec.get("title") or "").strip() or (rec.get("description") or "").strip())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=os.path.join(
        os.getenv("LUX_BASEPATH", "/Users/lux/data-pipeline"),
        "data", "input", "nha"))
    parser.add_argument("--outdir", default=str(BACKEND_DIR / "sample_data" / "nha_mapped"),
                        help="Directory to write mapped Linked Art JSON files")
    parser.add_argument("--sources", default=",".join(SOURCES),
                        help=f"Comma-separated source subdirs ({', '.join(SOURCES)})")
    parser.add_argument("--count", type=int, default=400,
                        help="Total number of records to map, spread over sources (default 400)")
    parser.add_argument("--seed", type=int, default=None,
                        help="Random seed for sampling")
    parser.add_argument("--reset", action="store_true",
                        help="Reset the backend database before loading")
    parser.add_argument("--no-load", action="store_true",
                        help="Only write files; skip database loading")
    args = parser.parse_args()

    model.factory.base_url = NHA_NAMESPACE

    input_dir = Path(args.input)
    sources = [s.strip() for s in args.sources.split(",") if s.strip()]
    bad = [s for s in sources if s not in SOURCES]
    if bad or not sources:
        print(f"Unknown source(s): {', '.join(bad or sources)}. "
              f"Valid sources: {', '.join(SOURCES)}")
        sys.exit(1)
    for source in sources:
        if not (input_dir / source).is_dir():
            print(f"Input directory not found: {input_dir / source}")
            sys.exit(1)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    per_source = max(1, args.count // len(sources))
    rng = random.Random(args.seed)

    mappers = {}
    for source in sources:
        module_path, class_name, label = SOURCES[source]
        mapper_class = getattr(importlib.import_module(module_path), class_name)
        mappers[source] = mapper_class({
            "namespace": NHA_NAMESPACE,
            "name": f"nha-{source}",
            "collectionLabel": label,
            "all_configs": _StubConfigs(),
        })

    total_selected = mapped = 0
    for source in sources:
        all_files = list((input_dir / source).glob("*.json"))
        rng.shuffle(all_files)
        sample = []
        for path in all_files:
            if len(sample) >= per_source:
                break
            try:
                rec = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if has_image_and_title(rec):
                sample.append((path.name, rec))

        print(f"[{source}] selected {len(sample)} image+title records "
              f"from {len(all_files)} candidates")
        total_selected += len(sample)

        for name, rec in sample:
            result = mappers[source].transform({"data": rec})
            if not result or not result.get("data"):
                continue
            record_id = result.get("identifier") or name[:-5]  # strip .json
            out_path = outdir / f"{source}_{record_id}.json"
            out_path.write_text(
                json.dumps(result["data"], indent=2, ensure_ascii=False),
                encoding="utf-8")
            mapped += 1

    if not mapped:
        print("No records mapped")
        sys.exit(1)
    print(f"Mapped {mapped}/{total_selected} records -> {outdir}")

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