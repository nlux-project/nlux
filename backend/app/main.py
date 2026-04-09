from __future__ import annotations

import json
from typing import Optional
from urllib.parse import unquote, quote

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy import text

from .config import settings
from .database import Base, engine, get_db
from .models import Record
from .search import search_records, SCOPE_TYPES

app = FastAPI(title="nlux-backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_methods=["GET"],
    allow_headers=["*"],
)

CONTEXT_SEARCH = "https://linked.art/ns/v1/search.json"
CONTEXT_LINKED_ART = "https://linked.art/ns/v1/linked-art.json"

SCOPE_LABELS = {
    "item": "Objects",
    "work": "Works",
    "set": "Sets",
    "agent": "People & Groups",
    "place": "Places",
    "concept": "Concepts",
    "event": "Events",
}

SCOPE_SUMMARIES = {
    "item": "Physical and digital objects",
    "work": "Works including texts, images, and information objects",
    "set": "Sets and collections",
    "agent": "People and groups",
    "place": "Places and geographic areas",
    "concept": "Concepts, types, and controlled vocabulary terms",
    "event": "Events, activities, and periods",
}

# HAL relation names per scope — maps to related-list query names
HAL_RELATIONS: dict[str, list[dict]] = {
    "item": [
        {"rel": "lux:itemArchive", "name": "memberItems", "relScope": "set"},
        {"rel": "lux:itemCreatedBy", "name": "createdItem", "relScope": "agent"},
    ],
    "work": [
        {"rel": "lux:workCreatedBy", "name": "createdWork", "relScope": "agent"},
        {"rel": "lux:workCarriedBy", "name": "carriedWork", "relScope": "item"},
    ],
    "agent": [
        {"rel": "lux:agentCreatedWork", "name": "createdWork", "relScope": "work"},
        {"rel": "lux:agentProducedItem", "name": "producedItem", "relScope": "item"},
        {"rel": "lux:agentRelatedPlaces", "name": "relatedToAgent", "relScope": "place"},
    ],
    "place": [
        {"rel": "lux:placeRelatedAgents", "name": "relatedToPlace", "relScope": "agent"},
        {"rel": "lux:placeRelatedItems", "name": "relatedToPlace", "relScope": "item"},
    ],
    "concept": [
        {"rel": "lux:conceptRelatedItems", "name": "aboutConcept", "relScope": "item"},
        {"rel": "lux:conceptRelatedAgents", "name": "aboutConcept", "relScope": "agent"},
    ],
    "set": [
        {"rel": "lux:setMembers", "name": "memberOf", "relScope": "item"},
    ],
    "event": [],
}


def _base() -> str:
    return settings.base_url.rstrip("/")


def _search_url(scope: str, q: str, page: int, page_length: int) -> str:
    return f"{_base()}/api/search/{scope}?q={quote(q)}&page={page}&pageLength={page_length}"


def _estimate_url(scope: str, q: str) -> str:
    return f"{_base()}/api/search-estimate/{scope}?q={quote(q)}"


def _related_url(scope: str, name: str, uri: str, page: int = 1) -> str:
    return f"{_base()}/api/related-list/{scope}?name={name}&uri={quote(uri)}&page={page}"


def _scope_for_type(linked_art_type: str) -> str:
    for scope, types in SCOPE_TYPES.items():
        if linked_art_type in types:
            return scope
    return "item"


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
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


# ---------------------------------------------------------------------------
# /data endpoints
# ---------------------------------------------------------------------------

@app.get("/data/results/persons")
def list_persons(
    page: int = Query(1, ge=1),
    pageLength: int = Query(20, alias="pageLength", ge=1),
    db: Session = Depends(get_db),
):
    q = db.query(Record).filter(Record.type == "Person")
    total = q.count()
    items = q.offset((page - 1) * pageLength).limit(pageLength).all()
    return {
        "@context": CONTEXT_LINKED_ART,
        "id": f"{_base()}/data/results/persons?page={page}&pageLength={pageLength}",
        "type": "OrderedCollectionPage",
        "totalItems": total,
        "orderedItems": [{"id": r.uri, "type": r.type} for r in items],
    }


@app.get("/data/results/places")
def list_places(
    page: int = Query(1, ge=1),
    pageLength: int = Query(20, alias="pageLength", ge=1),
    db: Session = Depends(get_db),
):
    q = db.query(Record).filter(Record.type == "Place")
    total = q.count()
    items = q.offset((page - 1) * pageLength).limit(pageLength).all()
    return {
        "@context": CONTEXT_LINKED_ART,
        "id": f"{_base()}/data/results/places?page={page}&pageLength={pageLength}",
        "type": "OrderedCollectionPage",
        "totalItems": total,
        "orderedItems": [{"id": r.uri, "type": r.type} for r in items],
    }


@app.get("/data/{uri:path}")
def get_record(
    uri: str,
    profile: Optional[str] = Query(None),
    lang: str = Query("en"),
    db: Session = Depends(get_db),
):
    decoded = unquote(uri)

    if decoded.startswith("results/"):
        return {
            "@context": CONTEXT_LINKED_ART,
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

    data = json.loads(record.data)

    # Inject HAL _links when no profile is requested
    if profile is None:
        scope = _scope_for_type(record.type)
        links: dict = {"self": {"href": record.uri}}
        for rel in HAL_RELATIONS.get(scope, []):
            links[rel["rel"]] = {
                "href": _related_url(rel["relScope"], rel["name"], record.uri),
                "_estimate": 0,
            }
        data["_links"] = links

    return data


# ---------------------------------------------------------------------------
# /api/search endpoints
# ---------------------------------------------------------------------------

@app.get("/api/search/{scope}")
def search(
    scope: str,
    q: str = Query(...),
    page: int = Query(1, ge=1),
    pageLength: Optional[int] = Query(None, alias="pageLength", ge=1),
    sort: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    page_length = min(
        pageLength or settings.page_length_default,
        settings.page_length_max,
    )
    items, total = search_records(db, q, scope, page, page_length)

    total_pages = max((total + page_length - 1) // page_length, 1)
    collection_url = _estimate_url(scope, q)

    result: dict = {
        "@context": CONTEXT_SEARCH,
        "id": _search_url(scope, q, page, page_length),
        "type": "OrderedCollectionPage",
        "partOf": [{
            "id": collection_url,
            "type": "OrderedCollection",
            "label": {"en": [SCOPE_LABELS.get(scope, scope)]},
            "summary": {"en": [SCOPE_SUMMARIES.get(scope, "")]},
            "totalItems": total,
        }],
        "orderedItems": items,
    }
    if page < total_pages:
        result["next"] = {
            "id": _search_url(scope, q, page + 1, page_length),
            "type": "OrderedCollectionPage",
        }
    if page > 1:
        result["prev"] = {
            "id": _search_url(scope, q, page - 1, page_length),
            "type": "OrderedCollectionPage",
        }
    return result


@app.get("/api/search-estimate/{scope}")
def search_estimate(
    scope: str,
    q: str = Query(...),
    db: Session = Depends(get_db),
):
    _, total = search_records(db, q, scope, page=1, page_length=0)
    page_length = settings.page_length_default
    total_pages = max((total + page_length - 1) // page_length, 1)

    result: dict = {
        "@context": CONTEXT_SEARCH,
        "id": _estimate_url(scope, q),
        "type": "OrderedCollection",
        "label": {"en": [SCOPE_LABELS.get(scope, scope)]},
        "summary": {"en": [SCOPE_SUMMARIES.get(scope, "")]},
        "totalItems": total,
    }
    if total > 0:
        result["first"] = {
            "id": _search_url(scope, q, 1, page_length),
            "type": "OrderedCollectionPage",
        }
        result["last"] = {
            "id": _search_url(scope, q, total_pages, page_length),
            "type": "OrderedCollectionPage",
        }
    return result


@app.get("/api/search-will-match")
def search_will_match(
    q: str = Query(...),
    db: Session = Depends(get_db),
):
    """
    Determine whether one or more named searches return at least one result.
    q can be a JSON object keyed by arbitrary names (each value is a search
    criteria dict), or a single criteria dict.

    Returns: {name: {"hasOneOrMoreResult": 1|0|-1, "isRelatedList": false}}
    """
    try:
        criteria = json.loads(q)
    except (json.JSONDecodeError, TypeError):
        criteria = {"default": {"text": q}}

    if not isinstance(criteria, dict):
        criteria = {"default": criteria}

    # If criteria values are dicts with search grammar, treat each as a named search.
    # Detect whether it's a map of named queries or a single query.
    first_val = next(iter(criteria.values()), None)
    if not isinstance(first_val, dict):
        # Single-level query — wrap it
        criteria = {"default": criteria}

    results = {}
    for name, sub_q in criteria.items():
        try:
            q_str = json.dumps(sub_q) if isinstance(sub_q, dict) else str(sub_q)
            scope = sub_q.get("_scope", "item") if isinstance(sub_q, dict) else "item"
            _, count = search_records(db, q_str, scope, page=1, page_length=1)
            results[name] = {
                "hasOneOrMoreResult": 1 if count > 0 else 0,
                "isRelatedList": False,
            }
        except Exception:
            results[name] = {"hasOneOrMoreResult": -1, "isRelatedList": False}

    return results


# ---------------------------------------------------------------------------
# /api/facets and /api/related-list
# ---------------------------------------------------------------------------

@app.get("/api/facets/{scope}")
def facets(
    scope: str,
    name: str = Query(...),
    q: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    pageLength: int = Query(20, alias="pageLength", ge=1),
    sort: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Returns empty facets — facet calculation not yet implemented."""
    id_str = f"{_base()}/api/facets/{scope}?name={name}&q={q or ''}&page={page}"
    return {
        "@context": CONTEXT_SEARCH,
        "id": id_str,
        "type": "OrderedCollectionPage",
        "orderedItems": [],
    }


@app.get("/api/related-list/{scope}")
def related_list(
    scope: str,
    name: str = Query(...),
    uri: str = Query(...),
    page: int = Query(1, ge=1),
    pageLength: Optional[int] = Query(None, alias="pageLength", ge=1),
    db: Session = Depends(get_db),
):
    """Returns empty related list — cross-entity linking not yet implemented."""
    return {
        "@context": CONTEXT_SEARCH,
        "id": _related_url(scope, name, uri, page),
        "type": "OrderedCollectionPage",
        "orderedItems": [],
    }


# ---------------------------------------------------------------------------
# /api/translate and /api/search-info
# ---------------------------------------------------------------------------

@app.get("/api/translate/{scope}")
def translate(
    scope: str,
    q: str = Query(...),
):
    query = json.dumps({"_scope": scope, "text": q, "_lang": "en"})
    from fastapi.responses import Response
    return Response(content=query, media_type="application/json")


@app.get("/api/search-info")
def search_info():
    """
    Describes available search terms, facet names, and sort options per scope.
    Minimal implementation — enough for lux-frontend to initialise.
    """
    scopes = list(SCOPE_TYPES.keys())
    search_by: dict = {}
    for scope in scopes:
        search_by[scope] = [
            {
                "name": "text",
                "targetScope": scope,
                "acceptsGroup": False,
                "acceptsTerm": True,
                "acceptsIdTerm": False,
                "onlyAcceptsId": False,
                "acceptsAtomicValue": True,
            }
        ]

    return {
        "searchBy": search_by,
        "facetBy": [],
        "sortBy": [
            {"name": "relevance", "type": "nonSemantic"},
        ],
    }


# ---------------------------------------------------------------------------
# /api/advanced-search-config
# ---------------------------------------------------------------------------

@app.get("/api/advanced-search-config")
def advanced_search_config():
    """
    Returns empty object — frontend falls back to its bundled defaults.
    Returning populated terms/options would require full AAT configuration.
    """
    return {}


# ---------------------------------------------------------------------------
# /api/stats and /api/tenant-status
# ---------------------------------------------------------------------------

@app.get("/api/stats")
def stats(db: Session = Depends(get_db)):
    counts = {}
    for scope, types in SCOPE_TYPES.items():
        count = (
            db.query(func.count(Record.uri))
            .filter(Record.type.in_(types))
            .scalar()
        ) or 0
        counts[scope] = count
    return {"estimates": {"searchScopes": counts}}


@app.get("/api/tenant-status")
def tenant_status():
    return {
        "prod": False,
        "readOnly": True,
        "codeVersion": "0.1.0",
        "dataVersion": None,
    }
