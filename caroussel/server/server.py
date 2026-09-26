#!/usr/bin/env python3
"""
NLUX Carousel server.

Serves a carousel API on top of the nlux backend API: it picks random
objects (with images) from a collection and normalises them into simple
slide items for the carousel frontend.

Usage:
    uvicorn server:app --port 8089        (from caroussel/server/)
    python server.py                      (equivalent)

Environment variables:
    NLUX_API            Base URL of the nlux backend (default http://localhost:8000)
    CAROUSEL_CONFIG     Path to carousel config JSON (default ../config/default.json)
"""
from __future__ import annotations

import base64
import json
import os
import random
import sys
import urllib.parse
from pathlib import Path
from typing import Any, Optional

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

SERVER_DIR = Path(__file__).resolve().parent
CAROUSEL_ROOT = SERVER_DIR.parent

NLUX_API = os.getenv("NLUX_API", "http://localhost:8000").rstrip("/")
CONFIG_PATH = Path(os.getenv(
    "CAROUSEL_CONFIG", CAROUSEL_ROOT / "config" / "default.json"))

DEFAULT_CONFIG: dict[str, Any] = {
    "server": {"port": 8089, "host": "0.0.0.0"},
    "carousel": {"interval": 10, "count": 5, "maxAge": 30,
                 "fullscreen": True, "lock": True},
    "collection": {"name": "teylers", "scope": "item",
                   "random": True, "seed": None},
    "theme": {
        "primary": "#2c5282", "background": "#f7fafc", "text": "#2d3748",
        "accent": "#ed8936", "card": "#ffffff", "cardBg": "#1a202c",
        "textColor": "#e2e8f0",
    },
}

app = FastAPI(title="NLUX Carousel API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


def load_config() -> dict[str, Any]:
    """Load the carousel config, falling back to built-in defaults."""
    config = json.loads(json.dumps(DEFAULT_CONFIG))  # deep copy
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return config
    for section, values in data.items():
        if isinstance(values, dict) and isinstance(config.get(section), dict):
            config[section].update(values)
        else:
            config[section] = values
    return config


CONFIG = load_config()

# A single lazily-created HTTP client (httpx clients are safe to reuse)
_client: Optional[httpx.Client] = None


def api() -> httpx.Client:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.Client(base_url=NLUX_API, timeout=20.0,
                               headers={"User-Agent": "nlux-carousel/1.0"})
    return _client


def image_token(image_url: str) -> str:
    """Encode an image URL the same way the nlux backend expects for /iiif/image."""
    return base64.urlsafe_b64encode(
        image_url.encode("utf-8")).decode("ascii").rstrip("=")


def proxied_image_url(image_url: str) -> str:
    return f"{NLUX_API}/iiif/image/{image_token(image_url)}"


# ---------------------------------------------------------------------------
# Linked Art -> carousel item normalisation
# ---------------------------------------------------------------------------

def _texts(nodes: Any) -> list[str]:
    """Collect non-empty _label values from a node or list of nodes."""
    if not isinstance(nodes, list):
        nodes = [nodes]
    out = []
    for node in nodes:
        if isinstance(node, dict):
            label = node.get("_label")
            if label:
                out.append(label)
    return out


def _first_image_url(doc: dict) -> Optional[str]:
    for rep in doc.get("representation", []) or []:
        for digital in rep.get("digitally_shown_by", []) or []:
            for ap in digital.get("access_point", []) or []:
                if isinstance(ap, dict) and ap.get("id"):
                    return ap["id"]
    return None


def _display_date(doc: dict) -> Optional[str]:
    prod = doc.get("produced_by") or {}
    ts = prod.get("timespan") if isinstance(prod, dict) else None
    if not isinstance(ts, dict):
        return None
    # Prefer the "Display Title" name the mapper attaches to the timespan
    for name in ts.get("identified_by", []) or []:
        if name.get("content"):
            return name["content"]
    # Fall back to the year of the start boundary
    start = ts.get("begin_of_the_begin")
    if isinstance(start, str) and len(start) >= 4:
        return start[:4]
    return None


def _detail_url(doc: dict) -> Optional[str]:
    """The museum's own object page, if the pipeline attached one.

    Some mappers (Huis van Hilde) also attach a findspot or site page;
    webpages labelled "Object page at …" are preferred over those.
    """
    fallback: Optional[str] = None
    for subject in doc.get("subject_of", []) or []:
        for digital in subject.get("digitally_carried_by", []) or []:
            for ap in digital.get("access_point", []) or []:
                if isinstance(ap, dict) and ap.get("id"):
                    if (digital.get("_label") or "").startswith("Object page"):
                        return ap["id"]
                    if fallback is None:
                        fallback = ap["id"]
    return fallback


def normalize_item(doc: dict, credit: Optional[str] = None) -> Optional[dict[str, Any]]:
    """Turn a Linked Art record into a flat carousel item.

    `credit` is the holding institution, taken from the collection config
    (falls back to the collection label).
    """
    uri = doc.get("id")
    if not uri:
        return None
    image_url = _first_image_url(doc)
    if not image_url:
        return None  # the carousel needs images

    prod = doc.get("produced_by") if isinstance(doc.get("produced_by"), dict) else {}

    creators = _texts(prod.get("carried_out_by"))
    seen: set[str] = set()
    unique_creators = [c for c in creators if not (c in seen or seen.add(c))]

    title = (doc.get("_label") or "").strip()
    if not title or title.lower() == "zonder titel":
        return None  # untitled objects are not shown in the carousel
    classification = _texts(doc.get("classified_as"))
    materials = _texts(doc.get("made_of"))
    techniques = _texts(prod.get("technique"))
    date = _display_date(doc)

    # Accession number, if present
    accession = None
    for ident in doc.get("identified_by", []) or []:
        if isinstance(ident, dict) and ident.get("classified_as"):
            for cls in ident["classified_as"]:
                if cls.get("id") == "http://vocab.getty.edu/aat/300312355":
                    accession = ident.get("content")

    return {
        "uri": uri,
        "id": uri.rsplit("/", 1)[-1],
        "type": doc.get("type"),
        "title": title,
        "creator": "; ".join(unique_creators[:3]) if unique_creators else None,
        "date": date,
        "classification": "; ".join(classification[:2]) if classification else None,
        "material": "; ".join(materials[:3]) if materials else None,
        "technique": "; ".join(techniques[:3]) if techniques else None,
        "accession": accession,
        "image": proxied_image_url(image_url),
        "detail_url": _detail_url(doc),
        "credit": credit,
    }


# ---------------------------------------------------------------------------
# NLUX API helpers
# ---------------------------------------------------------------------------

def collections_config() -> dict[str, Any]:
    """Named collections from the config; falls back to the legacy flat
    single-collection block for older config files."""
    cols = CONFIG.get("collections")
    if isinstance(cols, dict) and cols:
        return cols
    flat = CONFIG.get("collection") or {}
    return {flat.get("name", "default"): flat}


def resolve_collection(name: Optional[str]) -> tuple[str, dict[str, Any]]:
    """Resolve a collection by name (None -> configured default)."""
    cols = collections_config()
    if name is None:
        name = CONFIG.get("default_collection") or next(iter(cols))
    if name not in cols:
        available = ", ".join(sorted(cols))
        raise HTTPException(
            status_code=404,
            detail=f"Onbekende collectie: '{name}'. Beschikbare collecties: {available}",
        )
    return name, cols[name]


def search_item_uris(scope: str, query: Optional[dict[str, Any]] = None,
                      uri_prefix: Optional[str] = None) -> list[dict[str, str]]:
    """Return all image-bearing {id,type} stubs for a scope (paginates).

    `uri_prefix` optionally restricts stubs to one institution's URI
    namespace, so multiple collections can share a single backend DB.
    """
    criteria = dict(query or {})
    criteria.setdefault("hasDigitalImage", True)
    criteria["_scope"] = scope
    query = json.dumps(criteria)
    stubs: list[dict[str, str]] = []
    page = 1
    try:
        while True:
            resp = api().get(f"/api/search/{scope}", params={
                "q": query, "page": page, "pageLength": 100})
            resp.raise_for_status()
            data = resp.json()
            page_items = data.get("orderedItems", [])
            stubs.extend(page_items)
            total = data.get("partOf", [{}])[0].get("totalItems", len(stubs))
            if len(stubs) >= total or not page_items:
                break
            page += 1
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"NLUX API unreachable: {exc}")
    if uri_prefix:
        stubs = [s for s in stubs if str(s.get("id", "")).startswith(uri_prefix)]
    return stubs


def fetch_record(uri: str) -> Optional[dict]:
    try:
        # URI-quote the whole record URI: fhm ids contain '?' (their
        # namespace is a search-query URL), which would otherwise be sent
        # as a real query string and drop the id suffix.
        quoted = urllib.parse.quote(uri, safe="")
        resp = api().get(f"/data/{quoted}")
        if resp.status_code != 200:
            return None
        return resp.json()
    except httpx.HTTPError:
        return None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    try:
        resp = api().get("/health")
        ok = resp.status_code == 200
        nlux = resp.json() if ok else {}
    except httpx.HTTPError:
        ok, nlux = False, {}
    return {"status": "ok" if ok else "degraded", "nlux_api": nlux}


@app.get("/api/config")
def get_config():
    """Carousel configuration for the frontend."""
    default = CONFIG.get("default_collection") or next(iter(collections_config()))
    return {
        "carousel": CONFIG.get("carousel", {}),
        "collection": collections_config().get(default, {}),
        "collections": collections_config(),
        "default_collection": default,
        "theme": CONFIG.get("theme", {}),
        "nlux_api": NLUX_API,
        "total_items": _total_cache["items"],
    }


_total_cache: dict[str, Any] = {"items": 0}


@app.get("/api/carousel")
def get_carousel(
    count: int = Query(None, ge=1, le=50),
    scope: str = Query(None),
    seed: str = Query(None),
    collection: str = Query(None),
):
    """Return `count` random image-bearing objects for the carousel.

    The collection is chosen by name (see the `collections` config section);
    without a `collection` parameter the configured default is used.
    """
    collection_name, col = resolve_collection(collection)
    scope = scope or col.get("scope", "item")
    count = count or CONFIG.get("carousel", {}).get("count", 5)

    stubs = search_item_uris(scope, col.get("query"), col.get("uri_prefix"))
    _total_cache["items"] = len(stubs)
    if not stubs:
        raise HTTPException(status_code=502,
                            detail=f"No image-bearing objects found for "
                                  f"collection '{collection_name}' (scope '{scope}'). "
                                  f"Has its data been loaded into the backend DB?")

    rng = random.Random(seed if seed is not None else None)
    rng.shuffle(stubs)

    # Walk the shuffled stubs until we have `count` displayable items.
    # Untitled objects (no _label / "Zonder titel") and records without a
    # usable image are skipped, so we may need to look at more than `count`.
    items = []
    credit = col.get("credit") or col.get("label")
    for stub in stubs:
        if len(items) >= count:
            break
        doc = fetch_record(stub["id"])
        if doc is None:
            continue
        item = normalize_item(doc, credit=credit)
        if item:
            items.append(item)

    return {
        "collection": collection_name,
        "label": col.get("label"),
        "scope": scope,
        "count": len(items),
        "total_available": len(stubs),
        "seed": seed,
        "items": items,
    }


# Serve the built frontend (caroussel/frontend/dist) when it exists.
DIST_DIR = CAROUSEL_ROOT / "frontend" / "dist"
if DIST_DIR.is_dir():
    app.mount("/", StaticFiles(directory=DIST_DIR, html=True), name="dist")


if __name__ == "__main__":
    import uvicorn

    server_cfg = CONFIG.get("server", {})
    port = int(os.getenv("PORT", server_cfg.get("port", 8089)))
    host = os.getenv("HOST", server_cfg.get("host", "0.0.0.0"))
    print(f"NLUX Carousel server -> http://{host}:{port}")
    print(f"  NLUX API:  {NLUX_API}")
    print(f"  Config:    {CONFIG_PATH}")
    print(f"  Frontend:  {'built (dist served)' if DIST_DIR.is_dir() else 'not built (use vite dev server)'}")
    uvicorn.run(app, host=host, port=port, log_level="info")