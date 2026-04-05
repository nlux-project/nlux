from __future__ import annotations

import json
from typing import Optional
from urllib.parse import unquote

from fastapi import FastAPI, Depends, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy import text

from .config import settings
from .database import Base, engine, get_db
from .models import Record
from .schemas import SearchResponse
from .search import search_records

app = FastAPI(title="nlux-backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Linked Art types grouped into the scopes lux-frontend expects
SCOPE_TYPES = {
    "item": ["HumanMadeObject", "DigitalObject"],
    "work": ["LinguisticObject", "VisualItem", "InformationObject"],
    "set": ["Set"],
    "agent": ["Person", "Group", "Actor"],
    "place": ["Place"],
    "concept": ["Type", "Material", "Language", "MeasurementUnit", "Currency", "Concept"],
    "event": ["Activity", "Period", "Event", "Move", "Acquisition"],
}


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    # Create FTS5 virtual table for SQLite
    if settings.database_url.startswith("sqlite"):
        with engine.connect() as conn:
            conn.execute(text(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS records_fts
                USING fts5(search_text, content='records', content_rowid='rowid')
                """
            ))
            conn.commit()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/data/results/persons")
def list_persons(
    page: int = Query(0, ge=0),
    pageLength: int = Query(20, alias="pageLength", ge=1),
    db: Session = Depends(get_db),
):
    """Return an OrderedCollectionPage of all Person records."""
    q = db.query(Record).filter(Record.type == "Person")
    total = q.count()
    items = q.offset(page * pageLength).limit(pageLength).all()
    return {
        "@context": "https://linked.art/ns/v1/linked-art.json",
        "id": f"/data/results/persons?page={page}&pageLength={pageLength}",
        "type": "OrderedCollectionPage",
        "totalItems": total,
        "orderedItems": [
            {"id": r.uri, "type": r.type, "_label": r.label}
            for r in items
        ],
    }


@app.get("/data/results/places")
def list_places(
    page: int = Query(0, ge=0),
    pageLength: int = Query(20, alias="pageLength", ge=1),
    db: Session = Depends(get_db),
):
    """Return an OrderedCollectionPage of all Place records."""
    q = db.query(Record).filter(Record.type == "Place")
    total = q.count()
    items = q.offset(page * pageLength).limit(pageLength).all()
    return {
        "@context": "https://linked.art/ns/v1/linked-art.json",
        "id": f"/data/results/places?page={page}&pageLength={pageLength}",
        "type": "OrderedCollectionPage",
        "totalItems": total,
        "orderedItems": [
            {"id": r.uri, "type": r.type, "_label": r.label}
            for r in items
        ],
    }


@app.get("/data/{uri:path}")
def get_record(uri: str, db: Session = Depends(get_db)):
    # FastAPI path param captures everything; also handle URL-encoded ids
    decoded = unquote(uri)

    # LUX internal collection paths (e.g. results/collections/all) are not
    # real Linked Art records — return an empty OrderedCollection stub so
    # the frontend doesn't crash with a 404.
    if decoded.startswith("results/"):
        return {
            "@context": "https://linked.art/ns/v1/linked-art.json",
            "id": decoded,
            "type": "OrderedCollection",
            "totalItems": 0,
            "orderedItems": [],
        }

    record = db.query(Record).filter(
        (Record.uri == decoded) | (Record.uri == uri)
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return json.loads(record.data)


@app.get("/api/search/{scope}", response_model=SearchResponse)
def search(
    scope: str,
    q: str = Query(..., description="Search query string"),
    page: int = Query(0, ge=0),
    pageLength: Optional[int] = Query(None, alias="pageLength", ge=1),
    db: Session = Depends(get_db),
):
    items, total = search_records(db, q, scope, page, pageLength)
    collection_id = f"/api/search/{scope}?q={q}"
    return SearchResponse(
        id=f"{collection_id}&page={page}",
        totalItems=total,
        orderedItems=items,
        partOf=[{"id": collection_id, "type": "OrderedCollection", "totalItems": total}],
    )


@app.get("/api/stats")
def stats(db: Session = Depends(get_db)):
    """Record counts per scope — used by lux-frontend landing page infographics."""
    counts = {}
    for scope, types in SCOPE_TYPES.items():
        count = (
            db.query(func.count(Record.uri))
            .filter(Record.type.in_(types))
            .scalar()
        ) or 0
        counts[scope] = count
    return {"estimates": {"searchScopes": counts}}


@app.get("/api/translate/{scope}")
def translate(
    scope: str,
    q: str = Query(..., description="Simple search query string"),
):
    """
    Translate a simple search string into a LUX advanced query JSON string.
    The frontend uses this when switching from simple to advanced search.
    """
    query = json.dumps({"_scope": scope, "text": q})
    return Response(content=query, media_type="application/json")


@app.get("/api/advanced-search-config")
def advanced_search_config():
    """
    Return an empty object so the frontend spread leaves its local defaults
    intact. Returning {"terms": {}, "options": {}} would override them with
    empty dicts and crash the UI when it tries to access term properties.
    """
    return {}


@app.get("/api/facets/{scope}")
def facets(
    scope: str,
    q: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db),
):
    """Stub — returns empty facets with required id field for frontend pagination."""
    id_str = f"/api/facets/{scope}?q={q or ''}&page={page}"
    return {
        "id": id_str,
        "type": "OrderedCollectionPage",
        "orderedItems": [],
        "totalItems": 0,
        "partOf": [{"id": id_str, "type": "OrderedCollection", "totalItems": 0}],
    }


@app.get("/api/related-list/{scope}")
def related_list(
    scope: str,
    name: str = Query(...),
    uri: str = Query(...),
    page: int = Query(0, ge=0),
    pageLength: Optional[int] = Query(None, alias="pageLength", ge=1),
    db: Session = Depends(get_db),
):
    """Stub — returns empty related list. Implement in Phase 1."""
    return {
        "id": f"/api/related-list/{scope}?name={name}&uri={uri}&page={page}",
        "type": "OrderedCollectionPage",
        "totalItems": 0,
        "orderedItems": [],
    }


@app.get("/api/search-estimate/{scope}")
def search_estimate(
    scope: str,
    q: str = Query(...),
    db: Session = Depends(get_db),
):
    """Fast count estimate for a search query."""
    _, total = search_records(db, q, scope, page=0, page_length=0)
    return {"count": total}
