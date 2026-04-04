from __future__ import annotations

import json
from typing import Optional
from urllib.parse import unquote

from fastapi import FastAPI, Depends, HTTPException, Query
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


@app.get("/data/{uri:path}")
def get_record(uri: str, db: Session = Depends(get_db)):
    # FastAPI path param captures everything; also handle URL-encoded ids
    decoded = unquote(uri)
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
    return SearchResponse(
        id=f"/api/search/{scope}?q={q}&page={page}",
        totalItems=total,
        orderedItems=items,
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


@app.get("/api/advanced-search-config")
def advanced_search_config():
    """
    Returns minimal config; lux-frontend merges this with its own local defaults
    so empty dicts are safe — the UI will still work using its built-in config.
    """
    return {"terms": {}, "options": {}, "stopWords": []}


@app.get("/api/facets/{scope}")
def facets(scope: str, db: Session = Depends(get_db)):
    """Stub — returns empty facets. Full facet aggregation can be added in Phase 1."""
    return {"orderedItems": []}


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
