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
    """The museum's own object page, if the pipeline attached one."""
    for subject in doc.get("subject_of", []) or []:
        for digital in subject.get("digitally_carried_by", []) or []:
            for ap in digital.get("access_point", []) or []:
                if isinstance(ap, dict) and ap.get("id"):
                    return ap["id"]
    return None


def normalize_item(doc: dict) -> Optional[dict[str, Any]]:
    """Turn a Linked Art record into a flat carousel item."""
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

    title = doc.get("_label") or "Zonder titel"
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
        "credit": "Teylers Museum, Haarlem",
    }


# ---------------------------------------------------------------------------
# NLUX API helpers
# ---------------------------------------------------------------------------

def search_item_uris(scope: str) -> list[dict[str, str]]:
    """Return all image-bearing {id,type} stubs for a scope (paginates)."""
    query = json.dumps({"hasDigitalImage": True, "_scope": scope})
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
    return stubs


def fetch_record(uri: str) -> Optional[dict]:
    try:
        resp = api().get(f"/data/{uri}")
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
    return {
        "carousel": CONFIG.get("carousel", {}),
        "collection": CONFIG.get("collection", {}),
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
):
    """Return `count` random image-bearing objects for the carousel."""
    cfg = CONFIG.get("collection", {})
    scope = scope or cfg.get("scope", "item")
    count = count or CONFIG.get("carousel", {}).get("count", 5)

    stubs = search_item_uris(scope)
    _total_cache["items"] = len(stubs)
    if not stubs:
        raise HTTPException(status_code=502,
                            detail=f"No image-bearing objects found for scope '{scope}'")

    rng = random.Random(seed if seed is not None else None)
    picked = rng.sample(stubs, min(count, len(stubs)))

    items = []
    for stub in picked:
        doc = fetch_record(stub["id"])
        if doc is None:
            continue
        item = normalize_item(doc)
        if item:
            items.append(item)

    return {
        "collection": cfg.get("name", "teylers"),
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