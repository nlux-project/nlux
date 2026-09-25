# CLAUDE.md

This file provides guidance when working with code in this repository.

## Project Overview

**NLUX** is a Collections Discovery platform for the Dutch Cultural Heritage sector. Data is stored as [Linked Art](https://linked.art/) JSON-LD following CIDOC-CRM standards.

## Commands

### Task Runner

A top-level `Makefile` wraps all common commands with the correct environment
(`LUX_BASEPATH`, pinned Python 3.12 via `uv`):

```bash
make help           # list all targets
make backend-run    # API dev server on :8000
make pipeline       # full Teylers pipeline (harvest → load → reconcile → merge → export)
make test-backend   # backend test suite
```

### Local Development
#### Install backend

##### Important!
set ENV variable $LUX_BASEPATH (default: /Users/lux/data-pipeline) in any bash shell, script or command

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Docker (full stack with frontend)

```bash
docker compose up
```

### Docker (pipeline services — PostgreSQL + Redis)

```bash
docker compose --profile pipeline up
```

This adds `db` (PostgreSQL on 5432) and `redis` (on 6379) needed by the data-pipeline's reconcile/merge/export phases. Default `docker compose up` (api + frontend only) is unchanged.

### Data Pipeline (`data-pipeline/`)

```bash
cd data-pipeline

# Step 1 — Harvest raw records from Teylers Adlib API (no DB needed)
./harvest-teylers.sh

# Step 2 — Load into PostgreSQL datacache
python ./manage-data.py --load --teylers

# Step 3 — Reconcile against AAT authority data
python ./run-reconcile.py 0 1 --teylers

# Step 4 — Merge
python ./run-merge.py 0 1 --teylers

# Step 5 — Export to Linked Art JSONL
python ./run-export.py 0 1
```

Harvest AAT authority data (run once before first reconcile):
```bash
python ./run-harvest.py --aat
python ./manage-data.py --load-index --aat
```

### API Database Loading

After the pipeline exports JSONL to `$LUX_BASEPATH/data/output/latest/`:

```bash
# Load exported records into the nlux API database
python backend/scripts/load_data.py $LUX_BASEPATH/data/output/latest/

# Generate synthetic entity records
python backend/scripts/generate_agents.py     # persons + groups referenced by objects
python backend/scripts/generate_concepts.py   # concepts referenced by objects

# Reset the API database
python backend/scripts/reset.py
```

Convenience Docker loaders:
```bash
bash backend/scripts/load_all_to_docker.sh
```

### Carousel Display (`caroussel/`)

Full-screen slideshow of Teylers objects **with images**, served on :8089.

```bash
make carousel-load    # map raw Adlib records (image-bearing) into the API DB
make carousel-run    # build frontend, start backend :8000 + carousel server :8089
make carousel-test   # jsdom smoke test
# then open http://localhost:8089/
```

`backend/scripts/load_teylers_from_raw.py` runs the real pipeline mapper
(`pipeline/sources/museums/teylers/mapper.py`) over the raw Adlib harvest
(`$LUX_BASEPATH/data/input/teylers`), producing Linked Art with image
representations and IIIF manifests; see `caroussel/README.md`.

### Documentation

```bash
pip install mkdocs mkdocs-material
mkdocs serve           # local preview
mkdocs gh-deploy --force  # deploy to GitHub Pages
```

## Architecture

### Data Flow

```
Teylers Adlib API
  → data-pipeline/harvest-teylers.sh  (raw JSON to data-pipeline/input/)
  → manage-data.py --load             (PostgreSQL datacache)
  → run-reconcile.py                  (AAT + authority linking)
  → run-merge.py                      (entity deduplication)
  → run-export.py                     (Linked Art JSONL → $LUX_BASEPATH/data/output/latest/)
  → backend/scripts/load_data.py      (imports into nlux API database)
  → SQLite (dev) / PostgreSQL (prod)
  → FastAPI REST API
  → lux-frontend (React)
```

### Backend (`backend/app/`)

| File | Role |
|------|------|
| `main.py` | FastAPI app; all route definitions |
| `models.py` | SQLAlchemy ORM — single `Record` table |
| `database.py` | Engine config; WAL mode + FTS5 for SQLite |
| `search.py` | Full-text search — SQLite FTS5 vs. PostgreSQL `tsvector` + GIN |
| `config.py` | Pydantic Settings; reads `DATABASE_URL`, CORS origins, page defaults |
| `schemas.py` | Pydantic response models |

### Data Model

Every record maps to a single SQL row:

```python
Record(
    uri: str,          # primary key — Linked Art URI
    type: str,         # Linked Art class (e.g. HumanMadeObject)
    label: str,        # human-readable name
    search_text: str,  # concatenated text for FTS indexing
    data: str,         # full JSON-LD document (stringified)
)
```

### API Scopes → Linked Art Types

| Scope | Types |
|-------|-------|
| `item` | HumanMadeObject, DigitalObject |
| `work` | LinguisticObject, VisualItem, InformationObject |
| `set` | Set |
| `agent` | Person, Group, Actor |
| `place` | Place |
| `concept` | Type, Material, Language, MeasurementUnit, Currency, Concept |
| `event` | Activity, Period, Event, Move, Acquisition |

### Key API Endpoints

- `GET /health` — liveness
- `GET /data/{uri:path}` — full Linked Art record + HAL `_links` (omit `?profile=` for raw record)
- `GET /api/search/{scope}` — full-text search; returns Activity Streams `OrderedCollectionPage` with `{id, type}` stubs in `orderedItems`; supports `page`, `pageLength`, `sort`
- `GET /api/search-estimate/{scope}` — `OrderedCollection` with `totalItems`, `first`, `last`
- `GET /api/search-will-match` — named searches → `{hasOneOrMoreResult: 1|0|-1}`
- `GET /api/search-info` — available search terms, facets, sort options
- `GET /api/stats` — per-scope counts for landing page
- `GET /api/translate/{scope}` — simple text → LUX JSON search grammar
- `GET /api/tenant-status` — version / mode info
- `GET /api/advanced-search-config` — returns `{}` (frontend uses bundled defaults)
- `GET /api/facets/{scope}` — stub; real facet calculation not yet implemented
- `GET /api/related-list/{scope}` — stub; cross-entity linking not yet implemented

### Database Strategy

- **SQLite** (default dev): FTS5 virtual table, WAL journal mode
- **PostgreSQL** (production): `tsvector` column with GIN index; switch via `DATABASE_URL` env var

### Data Pipeline (`data-pipeline/`)

Yale LUX-based ETL pipeline adapted for Dutch CHE institutions. Configured for Teylers Museum (Adlib/Axiell API) and AAT (Getty). PostgreSQL + Redis are required for reconcile/merge/export phases; the harvest step only needs network access. See `data-pipeline/CLAUDE.md` for the internal architecture (slices, idmap, storage backends).

## Tech Stack

- Python 3.12+, FastAPI, Uvicorn, SQLAlchemy 2.x, Pydantic Settings 2.x
- SQLite with FTS5 (dev) / PostgreSQL with psycopg2 (prod)
- Docker + Docker Compose for full-stack deployment
- MkDocs Material for documentation (deployed via GitHub Actions)
