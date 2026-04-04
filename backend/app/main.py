import json
from urllib.parse import unquote

from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from .config import settings
from .database import Base, engine, get_db
from .models import Record
from .schemas import SearchResponse
from .search import search_records

app = FastAPI(title="nlux-backend", version="0.1.0")


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
    pageLength: int = Query(None, alias="pageLength", ge=1),
    db: Session = Depends(get_db),
    request_url: str = "",
):
    items, total = search_records(db, q, scope, page, pageLength)
    return SearchResponse(
        id=f"/api/search/{scope}?q={q}&page={page}",
        totalItems=total,
        orderedItems=items,
    )
