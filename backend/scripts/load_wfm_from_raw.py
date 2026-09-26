#!/usr/bin/env python3
"""
Generate Linked Art records for the Westfries Museum (WFM) from raw
Memorix harvest files, using the data-pipeline's WfmMapper (includes
image representations and object-page links), then load them into the
nlux backend database.

Only records with an image asset (thumb/download, mirroring the mapper's
image selection) and a usable title (kaart_title, description,
content_subject or record title) are selected, so every loaded object can
be displayed. Record URIs are minted under the WFM detail namespace
(https://westfriesmuseum.com/detail/), which is also what the carousel's
"wfm" collection filters on. Image URLs are served from
images.memorix.nl, which is already in the backend's trusted image hosts.

Usage (from backend/ or repo root):
    python scripts/load_wfm_from_raw.py [--count 400] [--seed 42]
        [--input DIR] [--outdir DIR] [--reset] [--no-load]

Input dir defaults to $LUX_BASEPATH/data/input/wfm (flat directory of
per-record JSON files; see harvest-wfm.sh).
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

WFM_NAMESPACE = "https://westfriesmuseum.com/detail/"


class _StubConfigs:
    """Minimal stand-in for pipeline Config, sufficient for WfmMapper."""

    internal_uri = os.getenv("NLUX_API", "http://localhost:8000") + "/data/"
    data_dir = "/tmp"
    globals = {}
    results = {"merged": {}}

    def get_idmap(self):
        return {}


def _clean(value) -> str:
    return str(value or "").strip()


def _metadata_values(metadata: dict, field: str) -> list[str]:
    value = metadata.get(field)
    if value is None:
        return []
    if isinstance(value, list):
        return [_clean(v) for v in value if _clean(v)]
    return [_clean(value)] if _clean(value) else []


def _asset_image_url(rec: dict) -> str:
    """First usable image URL, mirroring the mapper's asset selection."""
    for asset in rec.get("asset", []) or []:
        thumb = asset.get("thumb") or {}
        url = thumb.get("large") or asset.get("download") or thumb.get("medium")
        if url:
            return str(url)
    return ""


def _record_title(rec: dict, metadata: dict) -> str:
    """Usable title, mirroring the mapper's title chain (before the
    object-number / record-id fallbacks, which are not display-worthy)."""
    for field in ("kaart_title", "description", "content_subject"):
        values = _metadata_values(metadata, field)
        if values:
            return values[0]
    return _clean(rec.get("title"))


def has_image_and_title(rec: dict) -> bool:
    """True if the raw Memorix record has an image and a real title."""
    if not _asset_image_url(rec):
        return False
    metadata = {item.get("field"): item.get("value")
                for item in rec.get("metadata", []) or [] if item.get("field")}
    return bool(_record_title(rec, metadata))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=os.path.join(
        os.getenv("LUX_BASEPATH", "/Users/lux/data-pipeline"),
        "data", "input", "wfm"))
    parser.add_argument("--outdir", default=str(BACKEND_DIR / "sample_data" / "wfm_mapped"),
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

    model.factory.base_url = WFM_NAMESPACE

    input_dir = Path(args.input)
    if not input_dir.is_dir():
        print(f"Input directory not found: {input_dir}")
        sys.exit(1)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(args.seed)

    mapper_class = getattr(
        importlib.import_module("pipeline.sources.museums.wfm.mapper"),
        "WfmMapper")
    mapper = mapper_class({
        "namespace": WFM_NAMESPACE,
        "name": "wfm",
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

    print(f"[wfm] selected {len(sample)} image+title records "
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
        out_path = outdir / f"wfm_{record_id}.json"
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