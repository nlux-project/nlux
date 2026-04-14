# NLUX

## Wat is NLUX

NLUX is een Collections Discovery platform voor de Nederlandse Cultureel Erfgoed sector, gebouwd als drop-in backend vervanging voor `lux-marklogic`. Het implementeert het `lux-middletier` REST API contract en is volledig compatibel met de `lux-frontend` (React).

Data wordt opgeslagen als [Linked Art](https://linked.art/) JSON-LD conform CIDOC-CRM standaarden.

## Technologie

NLUX is gebouwd op project LUX (Yale Collections Discovery), beschikbaar op GitHub: https://github.com/project-lux

- Python 3.12+, FastAPI, Uvicorn, SQLAlchemy 2.x
- SQLite met FTS5 (ontwikkeling) / PostgreSQL met GIN-index (productie)
- Docker + Docker Compose voor volledige stack-uitrol
- Yale LUX ETL-pipeline voor dataverwerkng

## Data Pipeline

Records worden verwerkt via een Yale LUX-gebaseerde ETL-pipeline:

```
Teylers Adlib API
  → harvest-teylers.sh        (ruwe JSON)
  → enrich-teylers.py         (verrijking met Dimension, Material, etc.)
  → manage-data.py --load     (PostgreSQL datacache)
  → run-reconcile.py          (CHT + AAT authority linking)
  → run-merge.py              (entity deduplicatie)
  → run-export.py             (Linked Art JSONL)
  → backend/scripts/load_data.py  (import in nlux API database)
  → FastAPI REST API
  → lux-frontend (React)
```

### Thesauri / Authority data

NLUX koppelt records aan twee gecontroleerde vocabulaires:

| Thesaurus | Scope | URI-patroon |
|-----------|-------|-------------|
| **CHT** — Cultuurhistorische Thesaurus (RCE) | Primair voor Nederlandse collecties; hogere prioriteit (merge_order 8) | `https://data.cultureelerfgoed.nl/term/id/cht/` |
| **Getty AAT** — Art & Architecture Thesaurus | Brede meertalige dekking; fallback wanneer CHT geen match heeft | `http://vocab.getty.edu/aat/` |

CHT-termen bevatten vaak een `skos:exactMatch` naar AAT, zodat een CHT-koppeling automatisch ook de bijbehorende AAT-URI meeneemt via het `equivalent`-veld.

#### Eenmalige setup CHT-index

```bash
cd data-pipeline
uv run python harvest-cht.py                      # download alle CHT-termen via SPARQL
uv run python manage-data.py --load --cht          # laad in PostgreSQL datacache
uv run python manage-data.py --load-index --cht    # bouw label → CHT-URI SQLite-index
```

#### Eenmalige setup AAT-index

```bash
uv run python run-harvest.py --aat
uv run python manage-data.py --load-index --aat
```

## Lokale ontwikkeling

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Docker (volledige stack met frontend)

```bash
docker compose up
```

## Docker (pipeline services — PostgreSQL + Redis)

```bash
docker compose --profile pipeline up
```

## API endpoints (selectie)

| Endpoint | Omschrijving |
|----------|-------------|
| `GET /health` | Liveness check |
| `GET /data/{uri}` | Volledig Linked Art record + HAL `_links` |
| `GET /api/search/{scope}` | Volledige-tekst zoeken; geeft Activity Streams `OrderedCollectionPage` |
| `GET /api/stats` | Aantallen per scope (voor landingspagina) |

Scopes: `item`, `work`, `set`, `agent`, `place`, `concept`, `event`

## Licentie

Apache License 2.0
