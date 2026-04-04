# nlux-backend

Simplified backend for [NLUX](https://github.com/nlux-project/nlux), the Dutch Cultural Heritage Collections Discovery platform.

Replaces `lux-marklogic` with a lightweight Python/FastAPI service that implements the [lux-middletier](https://github.com/project-lux/lux-middletier) REST API contract, making it compatible with [lux-frontend](https://github.com/project-lux/lux-frontend).

Data is stored as [Linked Art](https://linked.art/) JSON-LD (CIDOC-CRM).

---

## Requirements

- Python 3.12+
- pip
- Docker + Docker Compose (optional)

---

## Quick start (local dev)

```bash
cd backend
pip install -r requirements.txt

# Load sample data
python scripts/load_data.py /path/to/lux_metadata/

# Start dev server (hot reload)
uvicorn app.main:app --reload
```

API is available at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

---

## Docker

```bash
# Build and run with SQLite (dev)
docker compose up

# Load data into the running container
docker compose exec api python scripts/load_data.py /path/to/lux_metadata/
```

For a PostgreSQL environment, uncomment the `db` service block in `docker-compose.yml` and set:

```bash
DATABASE_URL=postgresql://nlux:nlux@db:5432/nlux
```

---

## Configuration

| Environment variable | Default | Description |
|----------------------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./nlux.db` | SQLAlchemy connection string |
| `PAGE_LENGTH_DEFAULT` | `20` | Default search page size |
| `PAGE_LENGTH_MAX` | `100` | Maximum page size |

Variables can be set in a `.env` file in the `backend/` directory.

---

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness check |
| `GET` | `/data/{uri}` | Retrieve a Linked Art record by URI |
| `GET` | `/api/search/{scope}` | Full-text search |
| `GET` | `/api/search-estimate/{scope}` | Fast count estimate for a query |
| `GET` | `/api/stats` | Record counts per scope (landing page) |
| `GET` | `/api/advanced-search-config` | Search UI configuration |
| `GET` | `/api/facets/{scope}` | Faceted search (stub — Phase 1) |
| `GET` | `/api/related-list/{scope}` | Related entities (stub — Phase 1) |

### `GET /health`

```json
{"status": "ok"}
```

### `GET /data/{uri}`

Returns the full Linked Art JSON-LD document for the given record URI.

```bash
curl "http://localhost:8000/data/https://example.com/object/FK_0002"
```

### `GET /api/search/{scope}`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `q` | string | required | Search query |
| `page` | int | `0` | Page number (0-indexed) |
| `pageLength` | int | `20` | Results per page |

```bash
curl "http://localhost:8000/api/search/objects?q=Michelangelo&page=0&pageLength=10"
```

Response format (compatible with lux-middletier):

```json
{
  "@context": "https://linked.art/ns/v1/linked-art.json",
  "id": "/api/search/objects?q=Michelangelo&page=0",
  "type": "OrderedCollectionPage",
  "totalItems": 3,
  "orderedItems": [ ... ]
}
```

---

## Loading data

```bash
python scripts/load_data.py <directory>
```

Walks `<directory>` for `*.json` files, extracts `id`, `type`, `_label`, and text content for full-text indexing, and upserts each record into the database.

Test data: [jsoeterbroek/teylers_collection_research/lux_metadata](https://github.com/jsoeterbroek/teylers_collection_research/tree/main/lux_metadata)

---

## Database

| Environment | Database | Full-text search |
|-------------|----------|-----------------|
| Development | SQLite | FTS5 virtual table |
| Production | PostgreSQL | `tsvector` + GIN index |

The database is created automatically on first startup.

---

## Project structure

```
backend/
├── app/
│   ├── config.py      # Settings (reads environment variables)
│   ├── database.py    # SQLAlchemy engine and session
│   ├── models.py      # ORM model
│   ├── schemas.py     # Pydantic response schemas
│   ├── search.py      # FTS logic (SQLite / PostgreSQL)
│   └── main.py        # FastAPI app and routes
├── scripts/
│   └── load_data.py   # Data import CLI
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## Related

- [nlux-project/nlux](https://github.com/nlux-project/nlux) — main repo and documentation
- [project-lux/lux-frontend](https://github.com/project-lux/lux-frontend) — upstream frontend
- [project-lux/lux-middletier](https://github.com/project-lux/lux-middletier) — API contract this backend implements
- [linked.art](https://linked.art/) — data model standard

---

## Licence

Apache 2.0
