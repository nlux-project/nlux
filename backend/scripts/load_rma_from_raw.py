#!/usr/bin/env python3
"""
Generate Linked Art records for the Rijksmuseum Amsterdam (RMA) from raw
LOD harvest files and load them into the nlux backend database.

The raw records (resolver dumps from id.rijksmuseum.nl) are already
Linked Art, but their image data is only reachable through two stub
hops: `shows[*]` -> VisualItem -> `digitally_shown_by[*]` -> DigitalObject
-> `access_point[*].id` (a iiif.micr.io JPEG). For every sampled record
the loader resolves those hops and embeds the image under
`representation.digitally_shown_by`, the shape both the nlux backend's
hasDigitalImage check and the carousel's image extraction expect. The
IIIF URL is rewritten from /full/max/ to /full/800,/ (~75KB instead of
~4MB per image). The raw record's own id is kept (under
https://id.rijksmuseum.nl/), which is what the carousel's "rma"
collection filters on.

Titles (identified_by Name content) are stored as _label, the object
page in subject_of gets an "Object page at Rijksmuseum" _label so the
carousel prefers it as detail link, and current_owner (Group
"Rijksmuseum") makes the records findable via the institution's
full-text search. Images are served from iiif.micr.io, which must be in
the backend's trusted image hosts.

The rma input directory is a flat directory of ~835k JSON files, which
is pathologically slow to enumerate fully on APFS (a complete
os.listdir() scan takes ~16 minutes). This loader therefore streams
os.scandir() lazily and stops early once enough qualifying candidates
(title + shows stub) are collected; it never lists the full directory.

Usage (from backend/ or repo root):
    python scripts/load_rma_from_raw.py [--count 400] [--seed 42]
        [--input DIR] [--outdir DIR] [--scan-cap 12000] [--reset] [--no-load]

Input dir defaults to $LUX_BASEPATH/data/input/rma (flat directory of
per-record JSON files; see harvest-rma.sh). The seed makes the sampled
subset reproducible; which records survive enrichment also depends on
what the resolver returns at run time.
"""
import argparse
import json
import os
import random
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent

sys.path.insert(0, str(BACKEND_DIR))

RMA_LABEL = "Rijksmuseum"
RMA_PAGE_LABEL = "Object page at Rijksmuseum"
RESOLVER_ACCEPT = "application/ld+json"
IMAGE_SIZE_REWRITE = ("/full/max/", "/full/800,/")  # 16x lighter than max


def _get_json(url: str, timeout: int = 20, retries: int = 2):
    """GET a resolver resource as JSON; None on final failure."""
    for attempt in range(retries + 1):
        try:
            request = urllib.request.Request(
                url, headers={
                    "Accept": RESOLVER_ACCEPT,
                    "User-Agent": "nlux-rma-loader/1.0",
                })
            with urllib.request.urlopen(request, timeout=timeout) as resp:
                return json.load(resp)
        except Exception:
            if attempt == retries:
                return None
            time.sleep(1.0)
    return None


def _shrink_image_url(url: str) -> str:
    """Prefer the 800px IIIF variant over /full/max/ (~75KB vs ~4MB)."""
    return url.replace(*IMAGE_SIZE_REWRITE)


def _record_title(rec: dict) -> str:
    """First identified_by Name content."""
    for identifier in rec.get("identified_by", []) or []:
        if (isinstance(identifier, dict) and identifier.get("type") == "Name"
                and identifier.get("content")):
            return str(identifier["content"]).strip()
    return ""


def _shows_stubs(rec: dict) -> list[dict]:
    return [s for s in rec.get("shows", []) or []
            if isinstance(s, dict) and s.get("id")]


def has_image_stub_and_title(rec: dict) -> bool:
    """True if the raw record has a shows stub (image candidate) + title."""
    return bool(_shows_stubs(rec) and _record_title(rec))


class _ImageResolver:
    """Resolve VisualItem/DigitalObject stubs to an image URL, with a
    small cache for resources shared between records."""

    def __init__(self):
        self._cache: dict[str, str | None] = {}

    def image_url_for(self, stub: dict) -> str | None:
        url = self._image_url_from_visual_item(stub)
        if url is None and stub.get("id"):
            # stub -> full VisualItem; digitally_shown_by -> DigitalObject
            visual_item = _get_json(stub["id"])
            if isinstance(visual_item, dict):
                url = self._image_url_from_visual_item(visual_item)
        return url

    def _image_url_from_visual_item(self, vi: dict) -> str | None:
        for shown_by in vi.get("digitally_shown_by", []) or []:
            if not isinstance(shown_by, dict):
                continue
            for access_point in shown_by.get("access_point", []) or []:
                if isinstance(access_point, dict) and access_point.get("id"):
                    return _shrink_image_url(str(access_point["id"]))
            stub_id = shown_by.get("id")
            if not stub_id:
                continue
            if stub_id not in self._cache:
                digital = _get_json(stub_id)
                url = None
                for access_point in (digital or {}).get("access_point", []) or []:
                    if isinstance(access_point, dict) and access_point.get("id"):
                        url = _shrink_image_url(str(access_point["id"]))
                        break
                self._cache[stub_id] = url
            if self._cache[stub_id]:
                return self._cache[stub_id]
        return None


def _enrich_record(rec: dict, resolver: _ImageResolver) -> dict | None:
    """Return the display-ready record, or None if no image resolves."""
    title = _record_title(rec)
    image_url = None
    for stub in _shows_stubs(rec):
        image_url = resolver.image_url_for(stub)
        if image_url:
            break
    if not title or not image_url:
        return None

    rec["_label"] = title
    rec["representation"] = [{
        "type": "VisualItem",
        "digitally_shown_by": [{
            "type": "DigitalObject",
            "format": "image/jpeg",
            "access_point": [{"id": image_url, "type": "DigitalObject"}],
        }],
    }]
    if not rec.get("current_owner"):
        rec["current_owner"] = [{"type": "Group", "_label": RMA_LABEL}]
    # Label the object page so the carousel prefers it as detail link
    for subject in rec.get("subject_of", []) or []:
        for carried in subject.get("digitally_carried_by", []) or []:
            if (isinstance(carried, dict)
                    and carried.get("format") == "text/html"
                    and not carried.get("_label")):
                carried["_label"] = RMA_PAGE_LABEL
    return rec


def _scan_candidates(input_dir: Path, pool_target: int, scan_cap: int):
    """Stream scandir() lazily until pool_target qualifying records (or
    scan_cap files read); never a full listing of the flat 835k dir."""
    candidates, scanned = [], 0
    with os.scandir(input_dir) as entries:
        for entry in entries:
            if not entry.name.endswith(".json"):
                continue
            scanned += 1
            if scanned % 1000 == 0:
                print(f"[rma] scanned {scanned} files, "
                      f"{len(candidates)} candidates ...", flush=True)
            try:
                rec = json.loads(Path(entry.path).read_text(encoding="utf-8"))
            except Exception:
                continue
            if has_image_stub_and_title(rec):
                candidates.append(rec)
            if len(candidates) >= pool_target or scanned >= scan_cap:
                break
    return candidates, scanned


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=os.path.join(
        os.getenv("LUX_BASEPATH", "/Users/lux/data-pipeline"),
        "data", "input", "rma"))
    parser.add_argument("--outdir", default=str(BACKEND_DIR / "sample_data" / "rma_mapped"),
                        help="Directory to write enriched Linked Art JSON files")
    parser.add_argument("--count", type=int, default=400,
                        help="Number of records to load (default 400)")
    parser.add_argument("--seed", type=int, default=None,
                        help="Random seed for sampling")
    parser.add_argument("--scan-cap", type=int, default=12000,
                        help="Max raw files to read while sampling candidates")
    parser.add_argument("--reset", action="store_true",
                        help="Reset the backend database before loading")
    parser.add_argument("--no-load", action="store_true",
                        help="Only write files; skip database loading")
    args = parser.parse_args()

    input_dir = Path(args.input)
    if not input_dir.is_dir():
        print(f"Input directory not found: {input_dir}")
        sys.exit(1)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    pool_target = max(3 * args.count, 600)
    rng = random.Random(args.seed)
    candidates, scanned = _scan_candidates(input_dir, pool_target, args.scan_cap)
    print(f"[rma] scan done: {scanned} files read, {len(candidates)} candidates "
          f"(target {pool_target}; early exit, full dir not enumerated)", flush=True)
    if not candidates:
        print("No qualifying records found")
        sys.exit(1)

    rng.shuffle(candidates)
    resolver = _ImageResolver()
    written, failed = 0, 0
    with ThreadPoolExecutor(max_workers=6) as pool:
        for result in pool.map(lambda rec: _enrich_record(rec, resolver), candidates):
            if written >= args.count:
                break
            if result is None:
                failed += 1
                continue
            record_id = str(result.get("id", "")).rstrip("/").rsplit("/", 1)[-1] or "unknown"
            out_path = outdir / f"rma_{record_id}.json"
            out_path.write_text(
                json.dumps(result, indent=2, ensure_ascii=False),
                encoding="utf-8")
            written += 1
            if written % 25 == 0:
                print(f"[rma] {written}/{args.count} records enriched", flush=True)

    if not written:
        print("No records enriched (resolver unreachable / no images?)")
        sys.exit(1)
    print(f"[rma] wrote {written} records -> {outdir} "
          f"({failed} candidates without resolvable image skipped)", flush=True)

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