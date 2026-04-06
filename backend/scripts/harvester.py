#!/usr/bin/env python3
"""
NLUX Harvester — crawl online museum catalogs and produce Linked Art JSON files.

Usage:
    python scripts/harvester.py [--source teylers|boerhaave|huisvanhilde] [--augment]

Features:
  - Slow polite crawling (configurable delay, default 24s)
  - Progress tracking via SQLite state DB — safe to kill and resume
  - Per-source, per-collection output directories
  - Linked Art JSON-LD output with random 32-char IDs
  - Stub hooks for Wikipedia/Wikidata augmentation (not yet active)
  - Entity extraction: persons, places, groups saved as stubs alongside objects
"""

import argparse
import hashlib
import json
import logging
import re
import secrets
import sqlite3
import sys
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterator, Optional
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OUTPUT_BASE = Path(__file__).parent.parent / "harvested"
STATE_DB = Path(__file__).parent.parent / "harvested" / "state.db"

LINKED_ART_CONTEXT = "https://linked.art/ns/v1/linked-art.json"
AAT_PREFERRED_NAME  = "http://vocab.getty.edu/aat/300404670"
AAT_ACCESSION_NO    = "http://vocab.getty.edu/aat/300312355"
AAT_WEB_PAGE        = "http://vocab.getty.edu/aat/300264578"
AAT_DESCRIPTION     = "http://vocab.getty.edu/aat/300411780"

DEFAULT_DELAY = 24  # seconds between requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("harvester")


# ---------------------------------------------------------------------------
# State tracking
# ---------------------------------------------------------------------------

class StateDB:
    """SQLite-backed progress tracker."""

    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self._con = sqlite3.connect(str(path))
        self._con.row_factory = sqlite3.Row
        self._init()

    def _init(self):
        self._con.executescript("""
            CREATE TABLE IF NOT EXISTS records (
                source      TEXT NOT NULL,
                collection  TEXT NOT NULL,
                remote_id   TEXT NOT NULL,
                local_id    TEXT NOT NULL,
                url         TEXT NOT NULL,
                harvested_at TEXT,
                augmented_at TEXT,
                status      TEXT NOT NULL DEFAULT 'pending',
                PRIMARY KEY (source, collection, remote_id)
            );
            CREATE INDEX IF NOT EXISTS idx_status ON records(status);
        """)
        self._con.commit()

    def is_harvested(self, source: str, collection: str, remote_id: str) -> bool:
        row = self._con.execute(
            "SELECT status FROM records WHERE source=? AND collection=? AND remote_id=?",
            (source, collection, remote_id)
        ).fetchone()
        return row is not None and row["status"] in ("done", "error")

    def is_augmented(self, source: str, collection: str, remote_id: str) -> bool:
        row = self._con.execute(
            "SELECT augmented_at FROM records WHERE source=? AND collection=? AND remote_id=?",
            (source, collection, remote_id)
        ).fetchone()
        return row is not None and row["augmented_at"] is not None

    def register(self, source: str, collection: str, remote_id: str, url: str) -> str:
        """Register a record; return its stable local_id (create if new)."""
        row = self._con.execute(
            "SELECT local_id FROM records WHERE source=? AND collection=? AND remote_id=?",
            (source, collection, remote_id)
        ).fetchone()
        if row:
            return row["local_id"]
        local_id = secrets.token_hex(16)  # 32-char hex
        self._con.execute(
            "INSERT INTO records(source, collection, remote_id, local_id, url) VALUES(?,?,?,?,?)",
            (source, collection, remote_id, local_id, url)
        )
        self._con.commit()
        return local_id

    def mark_done(self, source: str, collection: str, remote_id: str):
        self._con.execute(
            "UPDATE records SET status='done', harvested_at=? WHERE source=? AND collection=? AND remote_id=?",
            (datetime.utcnow().isoformat(), source, collection, remote_id)
        )
        self._con.commit()

    def mark_error(self, source: str, collection: str, remote_id: str):
        self._con.execute(
            "UPDATE records SET status='error', harvested_at=? WHERE source=? AND collection=? AND remote_id=?",
            (datetime.utcnow().isoformat(), source, collection, remote_id)
        )
        self._con.commit()

    def mark_augmented(self, source: str, collection: str, remote_id: str):
        self._con.execute(
            "UPDATE records SET augmented_at=? WHERE source=? AND collection=? AND remote_id=?",
            (datetime.utcnow().isoformat(), source, collection, remote_id)
        )
        self._con.commit()

    def stats(self, source: str) -> dict:
        rows = self._con.execute(
            "SELECT status, COUNT(*) AS n FROM records WHERE source=? GROUP BY status",
            (source,)
        ).fetchall()
        return {r["status"]: r["n"] for r in rows}

    def pending_augmentation(self, source: str) -> list:
        return self._con.execute(
            "SELECT source, collection, remote_id, local_id FROM records "
            "WHERE source=? AND status='done' AND augmented_at IS NULL",
            (source,)
        ).fetchall()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def slugify(name: str) -> str:
    slug = name.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug


def fetch_html(url: str, timeout: int = 30) -> str:
    req = Request(url, headers={"User-Agent": "nlux-harvester/1.0 (research project)"})
    try:
        with urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            # detect encoding from Content-Type header
            ct = resp.headers.get("Content-Type", "")
            enc = "utf-8"
            m = re.search(r"charset=([\w-]+)", ct)
            if m:
                enc = m.group(1)
            try:
                return raw.decode(enc, errors="replace")
            except LookupError:
                return raw.decode("utf-8", errors="replace")
    except HTTPError as e:
        raise RuntimeError(f"HTTP {e.code} for {url}") from e
    except URLError as e:
        raise RuntimeError(f"URL error for {url}: {e.reason}") from e


def extract_text(html: str, tag: str, attrs: dict = None) -> list[str]:
    """Very simple tag extractor — no dependencies."""
    pattern = f"<{tag}[^>]*>(.*?)</{tag}>"
    return [re.sub(r"<[^>]+>", "", m).strip()
            for m in re.findall(pattern, html, re.DOTALL | re.IGNORECASE)]


def write_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def linked_art_stub(local_id: str, record_type: str, label: str,
                    accession: str, source_url: str, institution: str,
                    institution_id: str) -> dict:
    """Build a minimal Linked Art record shell."""
    return {
        "@context": LINKED_ART_CONTEXT,
        "id": f"urn:nlux:{local_id}",
        "type": record_type,
        "_label": label,
        "identified_by": [
            {
                "type": "Name",
                "content": label,
                "classified_as": [{"id": AAT_PREFERRED_NAME, "_label": "preferred name"}],
            },
            {
                "type": "Identifier",
                "content": accession,
                "classified_as": [{"id": AAT_ACCESSION_NO, "_label": "accession number"}],
                "assigned_by": [{"type": "AttributeAssignment", "carried_out_by": [
                    {"type": "Group", "_label": institution, "id": institution_id}
                ]}],
            },
        ],
        "subject_of": [{
            "type": "LinguisticObject",
            "digitally_carried_by": [{
                "type": "DigitalObject",
                "classified_as": [{"id": AAT_WEB_PAGE, "_label": "web page"}],
                "access_point": [{"id": source_url}],
                "format": "text/html",
                "identified_by": [{"type": "Name", "content": f"{institution} catalog page"}],
            }],
        }],
        "_harvest": {
            "source_url": source_url,
            "local_id": local_id,
            "harvested_at": datetime.utcnow().isoformat(),
            "augmented": False,
        },
    }


# ---------------------------------------------------------------------------
# Augmentation stubs (Wikipedia / Wikidata — not yet active)
# ---------------------------------------------------------------------------

def augment_wikipedia(record: dict) -> dict:
    """Placeholder: enrich record with Wikipedia data. Not yet implemented."""
    # TODO: search Wikipedia API for label, add sameAs / referred_to_by
    return record


def augment_wikidata(record: dict) -> dict:
    """Placeholder: enrich record with Wikidata. Not yet implemented."""
    # TODO: SPARQL query Wikidata for Q-item, add sameAs
    return record


# ---------------------------------------------------------------------------
# Base source class
# ---------------------------------------------------------------------------

@dataclass
class SourceConfig:
    name: str
    base_url: str
    institution_label: str
    institution_id: str
    collections: dict = field(default_factory=dict)  # {collection_name: list_url}


class BaseHarvester(ABC):
    def __init__(self, config: SourceConfig, state: StateDB,
                 delay: int = DEFAULT_DELAY, dry_run: bool = False):
        self.cfg = config
        self.state = state
        self.delay = delay
        self.dry_run = dry_run
        self.out_base = OUTPUT_BASE / config.name

    @abstractmethod
    def iter_collection(self, collection: str, list_url: str) -> Iterator[tuple[str, str]]:
        """Yield (remote_id, detail_url) for every item in a collection."""

    @abstractmethod
    def fetch_record(self, remote_id: str, detail_url: str,
                     collection: str, local_id: str) -> dict:
        """Fetch and return a Linked Art dict for one record."""

    def run(self, augment: bool = False):
        log.info(f"=== Source: {self.cfg.name} ===")
        for collection, list_url in self.cfg.collections.items():
            log.info(f"  Collection: {collection}  ({list_url})")
            self._harvest_collection(collection, list_url)

        if augment:
            self._augment_pending()

        stats = self.state.stats(self.cfg.name)
        log.info(f"  Stats: {stats}")

    def _harvest_collection(self, collection: str, list_url: str):
        out_dir = self.out_base / collection
        seen = 0
        harvested = 0

        for remote_id, detail_url in self.iter_collection(collection, list_url):
            seen += 1
            if self.state.is_harvested(self.cfg.name, collection, remote_id):
                log.info(f"    [{seen}] SKIP (already done): {remote_id}")
                continue

            local_id = self.state.register(self.cfg.name, collection, remote_id, detail_url)
            log.info(f"    [{seen}] Fetching {remote_id}  →  {detail_url}")

            if self.dry_run:
                log.info("    DRY RUN — skipping actual fetch")
                continue

            try:
                record = self.fetch_record(remote_id, detail_url, collection, local_id)
                out_path = out_dir / f"{remote_id}.json"
                write_json(out_path, record)
                self.state.mark_done(self.cfg.name, collection, remote_id)
                harvested += 1
                log.info(f"    Wrote {out_path.relative_to(OUTPUT_BASE)}")
            except Exception as exc:
                log.error(f"    ERROR on {remote_id}: {exc}")
                self.state.mark_error(self.cfg.name, collection, remote_id)

            log.info(f"    Waiting {self.delay}s ...")
            time.sleep(self.delay)

        log.info(f"  Collection '{collection}': seen={seen}, newly harvested={harvested}")

    def _augment_pending(self):
        pending = self.state.pending_augmentation(self.cfg.name)
        if not pending:
            log.info("  No records pending augmentation.")
            return
        log.info(f"  Augmenting {len(pending)} records ...")
        for row in pending:
            collection = row["collection"]
            remote_id = row["remote_id"]
            local_id = row["local_id"]
            path = self.out_base / collection / f"{remote_id}.json"
            if not path.exists():
                log.warning(f"    Missing file for {remote_id}, skipping augmentation")
                continue
            record = json.loads(path.read_text(encoding="utf-8"))
            record = augment_wikipedia(record)
            record = augment_wikidata(record)
            record["_harvest"]["augmented"] = True
            write_json(path, record)
            self.state.mark_augmented(self.cfg.name, collection, remote_id)
            log.info(f"    Augmented {remote_id}")
            time.sleep(self.delay)


# ---------------------------------------------------------------------------
# Adlib AIS6 API harvester (Teylers + Boerhaave)
# ---------------------------------------------------------------------------
# Collection list_url format: "<database>|<detail_base_url>"
# e.g. "museum|https://teylers.adlibhosting.com/ais6/search/Details/collect"
# The API endpoint is <base_url>helper/GetSearchResult?Database=<db>&...
# ---------------------------------------------------------------------------

_LA_TYPE_BY_COLLECTION = {
    "books": "LinguisticObject",
    "library": "LinguisticObject",
    "document": "LinguisticObject",
    "drawings": "VisualItem",
    "prints": "VisualItem",
}

_IMAGE_FIELDS = ("reproduction.reference", "image_path", "image", "reproduction")


class AdlibAPIHarvester(BaseHarvester):
    """
    Harvester for Adlib / Axiell AIS6 JSON API.
    One API call returns up to API_LIMIT full records — no per-record detail
    page fetches needed.
    """

    API_LIMIT = 50

    def _api_url(self, db: str, start: int) -> str:
        base = self.cfg.base_url.rstrip("/")
        return (
            f"{base}/helper/GetSearchResult"
            f"?Database={db}&SearchStatement=all"
            f"&Limit={self.API_LIMIT}&StartFrom={start}"
        )

    @classmethod
    def _flatten_field(cls, key: str, value) -> list[tuple[str, str]]:
        """
        Recursively flatten an Adlib field value into (label, string) pairs.

        Handles three formats returned by the AIS6 API:
          - Plain scalar:   "KS 217"  →  [(key, "KS 217")]
          - Multilingual:   [{"lang": "nl-NL", "value": "Titel"}]  →  [(key, "Titel")]
          - Nested record:  [{"title": "De Amsterdamse Poort..."}]  →  [(key.title, "De Amst...")]
          - Deep nested:    [{"media.reference": {"reference_number": "x.jpg"}}]  →  recursive
        """
        if value is None or isinstance(value, bool):
            return []
        if isinstance(value, (int, float)):
            return [(key, str(value))]
        if isinstance(value, str):
            return [(key, value.strip())] if value.strip() else []
        if isinstance(value, list):
            result = []
            for item in value:
                result.extend(cls._flatten_field(key, item))
            return result
        if isinstance(value, dict):
            if "value" in value:
                # Multilingual format: {"lang": ..., "value": "..."}
                v = str(value["value"]).strip()
                return [(key, v)] if v else []
            # Nested Adlib sub-record: flatten each sub-field with dotted key
            result = []
            for sub_key, sub_val in value.items():
                result.extend(cls._flatten_field(f"{key}.{sub_key}", sub_val))
            return result
        return [(key, str(value))]

    @classmethod
    def _first_value(cls, raw: dict, *keys: str) -> str:
        """Return the first non-empty flattened value for any of the given keys."""
        for key in keys:
            v = raw.get(key)
            if v is not None:
                pairs = cls._flatten_field(key, v)
                if pairs:
                    return pairs[0][1]
        return ""

    def _guess_la_type(self, collection: str) -> str:
        return _LA_TYPE_BY_COLLECTION.get(collection, "HumanMadeObject")

    def _build_record(self, raw: dict, collection: str,
                      local_id: str, detail_url: str) -> dict:
        priref = str(raw.get("priref", "")) or str(raw.get("@priref", ""))
        # Title: try capitalised then lowercase key, then object_name fallback
        title = (
            self._first_value(raw, "Title", "title", "Object_name", "object_name", "name")
            or priref
        )

        record = linked_art_stub(
            local_id=local_id,
            record_type=self._guess_la_type(collection),
            label=title,
            accession=priref,
            source_url=detail_url,
            institution=self.cfg.institution_label,
            institution_id=self.cfg.institution_id,
        )

        # Attach all raw fields as LinguisticObject notes (flatten nested records)
        skip = {"priref", "@priref", "@attributes", "@selected"}
        notes = []
        for key, value in raw.items():
            if key in skip:
                continue
            for label, val_str in self._flatten_field(key, value):
                if val_str:
                    notes.append({
                        "type": "LinguisticObject",
                        "content": val_str,
                        "classified_as": [{"id": AAT_DESCRIPTION, "_label": label}],
                        "identified_by": [{"type": "Name", "content": label}],
                    })
        if notes:
            record.setdefault("referred_to_by", []).extend(notes)

        # Image: store URL only, never download. Only include if it looks like a URL.
        for img_field in _IMAGE_FIELDS:
            pairs = self._flatten_field(img_field, raw.get(img_field, []))
            for _, img_url in pairs:
                if img_url.startswith("http"):
                    record["representation"] = [{
                        "type": "VisualItem",
                        "digitally_shown_by": [{
                            "type": "DigitalObject",
                            "access_point": [{"id": img_url}],
                            "format": "image/jpeg",
                        }],
                    }]
                    break
            if "representation" in record:
                break

        return record

    # iter_collection / fetch_record are not used — _harvest_collection is overridden
    def iter_collection(self, collection: str, list_url: str) -> Iterator[tuple[str, str]]:
        return iter([])

    def fetch_record(self, remote_id: str, detail_url: str,
                     collection: str, local_id: str) -> dict:
        return {}

    def _harvest_collection(self, collection: str, list_url: str):
        """Batch-fetch via API; one call returns up to API_LIMIT full records."""
        db, detail_base = list_url.split("|", 1)
        out_dir = self.out_base / collection

        start = 1
        total: Optional[int] = None
        seen = 0
        harvested = 0

        while total is None or start <= total:
            api_url = self._api_url(db, start)
            log.debug(f"      API: {api_url}")
            try:
                raw_text = fetch_html(api_url)
                data = json.loads(raw_text)
            except Exception as exc:
                log.error(f"      API error at start={start}: {exc}")
                break

            if data.get("ErrorOccured"):
                log.error(f"      API returned error: {data}")
                break

            if total is None:
                total = data.get("Hits", 0)
                log.info(f"      Total records in '{collection}': {total}")

            batch = data.get("Result", {}).get("record", [])
            if not batch:
                break

            for raw_rec in batch:
                priref_raw = raw_rec.get("priref") or raw_rec.get("@priref")
                priref = str(priref_raw).strip() if priref_raw is not None else None
                if not priref:
                    continue

                seen += 1
                detail_url = f"{detail_base}/{priref}"

                if self.state.is_harvested(self.cfg.name, collection, priref):
                    log.info(f"    [{seen}/{total}] SKIP (already done): {priref}")
                    continue

                local_id = self.state.register(self.cfg.name, collection, priref, detail_url)
                log.info(f"    [{seen}/{total}] Processing {priref}")

                if self.dry_run:
                    log.info("    DRY RUN — skipping write")
                    continue

                try:
                    record = self._build_record(raw_rec, collection, local_id, detail_url)
                    out_path = out_dir / f"{priref}.json"
                    write_json(out_path, record)
                    self.state.mark_done(self.cfg.name, collection, priref)
                    harvested += 1
                    log.info(f"    Wrote {out_path.relative_to(OUTPUT_BASE)}")
                except Exception as exc:
                    log.error(f"    ERROR on {priref}: {exc}")
                    self.state.mark_error(self.cfg.name, collection, priref)

            start += self.API_LIMIT
            if total is not None and start <= total:
                log.info(f"    Waiting {self.delay}s ... ({seen}/{total} processed)")
                time.sleep(self.delay)

        log.info(f"  Collection '{collection}': seen={seen}, newly harvested={harvested}")


class TeylersHarvester(AdlibAPIHarvester):
    """Harvester for teylers.adlibhosting.com — Axiell AIS6 JSON API."""
    pass


# ---------------------------------------------------------------------------
# Boerhaave harvester (mmb-web.adlibhosting.com — same AIS6 engine)
# ---------------------------------------------------------------------------

class BoerhaaveHarvester(AdlibAPIHarvester):
    """Harvester for mmb-web.adlibhosting.com — Axiell AIS6 JSON API.
    Field values use multilingual dicts: [{"lang": "nl-NL", "value": "..."}]
    which _get_field / _get_all_values already handle transparently.
    """
    pass


# ---------------------------------------------------------------------------
# Huis van Hilde harvester (collectie.huisvanhilde.nl)
# ---------------------------------------------------------------------------

class HuisVanHildeHarvester(BaseHarvester):
    """
    Harvester for collectie.huisvanhilde.nl.
    The site uses Axiell Collections Online (EMu-based).
    We crawl the search results and detail pages.
    """

    ITEM_RE = re.compile(
        r'href="(/nl/Detail/objects/(?P<rid>[^"?]+))"', re.IGNORECASE
    )
    TITLE_RE = re.compile(r'<h1[^>]*>(.*?)</h1>', re.DOTALL | re.IGNORECASE)
    FIELD_RE = re.compile(
        r'<dt[^>]*>(.*?)</dt>\s*<dd[^>]*>(.*?)</dd>',
        re.DOTALL | re.IGNORECASE,
    )

    def iter_collection(self, collection: str, list_url: str) -> Iterator[tuple[str, str]]:
        page = 1
        seen_ids: set = set()
        while True:
            url = f"{list_url}?page={page}" if page > 1 else list_url
            log.debug(f"      Page {page}: {url}")
            try:
                html = fetch_html(url)
            except RuntimeError as e:
                log.error(f"      Failed to fetch page {page}: {e}")
                break
            found = 0
            for m in self.ITEM_RE.finditer(html):
                rid = m.group("rid")
                if rid in seen_ids:
                    continue
                seen_ids.add(rid)
                detail_url = urljoin(self.cfg.base_url, m.group(1))
                yield rid, detail_url
                found += 1
            if found == 0:
                break
            page += 1
            time.sleep(self.delay)

    def fetch_record(self, remote_id: str, detail_url: str,
                     collection: str, local_id: str) -> dict:
        html = fetch_html(detail_url)

        title = ""
        m = self.TITLE_RE.search(html)
        if m:
            title = re.sub(r"<[^>]+>", "", m.group(1)).strip()

        record = linked_art_stub(
            local_id=local_id,
            record_type="HumanMadeObject",
            label=title or remote_id,
            accession=remote_id,
            source_url=detail_url,
            institution=self.cfg.institution_label,
            institution_id=self.cfg.institution_id,
        )

        notes = []
        for m in self.FIELD_RE.finditer(html):
            key = re.sub(r"<[^>]+>", "", m.group(1)).strip()
            val = re.sub(r"<[^>]+>", "", m.group(2)).strip()
            if key and val:
                notes.append({
                    "type": "LinguisticObject",
                    "content": val,
                    "classified_as": [{"id": AAT_DESCRIPTION, "_label": key}],
                    "identified_by": [{"type": "Name", "content": key}],
                })
        if notes:
            record.setdefault("referred_to_by", []).extend(notes)

        return record


# ---------------------------------------------------------------------------
# Source registry — add new sources here
# ---------------------------------------------------------------------------

SOURCES = {
    "teylers": (
        TeylersHarvester,
        SourceConfig(
            name="teylers",
            base_url="https://teylers.adlibhosting.com/ais6/",
            institution_label="Teylers Museum",
            institution_id="https://teylers.adlibhosting.com/nlux/group/teylers-museum",
            # Format: "<Adlib database name>|<detail page base URL>"
            collections={
                "museum": "museum|https://teylers.adlibhosting.com/ais6/search/Details/collect",
                "books":  "document|https://teylers.adlibhosting.com/ais6/search/Details/document",
            },
        ),
    ),
    "boerhaave": (
        BoerhaaveHarvester,
        SourceConfig(
            name="boerhaave",
            base_url="https://mmb-web.adlibhosting.com/",
            institution_label="Rijksmuseum Boerhaave",
            institution_id="https://mmb-web.adlibhosting.com/nlux/group/rijksmuseum-boerhaave",
            # Format: "<Adlib database name>|<detail page base URL>"
            collections={
                "museum": "collect|https://mmb-web.adlibhosting.com/search/Details/collect",
            },
        ),
    ),
    "huisvanhilde": (
        HuisVanHildeHarvester,
        SourceConfig(
            name="huisvanhilde",
            base_url="https://collectie.huisvanhilde.nl",
            institution_label="Huis van Hilde",
            institution_id="https://collectie.huisvanhilde.nl/nlux/group/huis-van-hilde",
            collections={
                "objects": "https://collectie.huisvanhilde.nl/nl/collectie",
            },
        ),
    ),
}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args():
    p = argparse.ArgumentParser(description="NLUX museum catalog harvester")
    p.add_argument(
        "--source", choices=list(SOURCES.keys()) + ["all"],
        default="all",
        help="Which source to harvest (default: all)",
    )
    p.add_argument(
        "--delay", type=int, default=DEFAULT_DELAY,
        help=f"Seconds to wait between requests (default: {DEFAULT_DELAY})",
    )
    p.add_argument(
        "--augment", action="store_true",
        help="Run augmentation pass (Wikipedia/Wikidata) on already-harvested records",
    )
    p.add_argument(
        "--dry-run", action="store_true",
        help="Discover records but do not fetch detail pages",
    )
    p.add_argument(
        "--stats", action="store_true",
        help="Print harvesting stats and exit",
    )
    return p.parse_args()


def main():
    args = parse_args()
    state = StateDB(STATE_DB)

    if args.stats:
        for src_name in SOURCES:
            s = state.stats(src_name)
            log.info(f"{src_name}: {s}")
        return

    sources_to_run = list(SOURCES.keys()) if args.source == "all" else [args.source]

    for src_name in sources_to_run:
        cls, cfg = SOURCES[src_name]
        harvester = cls(cfg, state, delay=args.delay, dry_run=args.dry_run)
        try:
            harvester.run(augment=args.augment)
        except KeyboardInterrupt:
            log.info("Interrupted — state saved, safe to resume.")
            sys.exit(0)


if __name__ == "__main__":
    main()
