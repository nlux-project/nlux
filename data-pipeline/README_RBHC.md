# Rijksmuseum Boerhaave Collection Source (RBHC)

Integration of the Rijksmuseum Boerhaave public collection database into the NLUX data pipeline.

## Harvesting

The source uses the Axiell AIS6 Adlib WebAPI:

```text
https://mmb-web.adlibhosting.com/ais6/webapi/wwwopac.ashx
```

- Source abbreviation: `rbhc`
- Database name: `collect`
- Public search page: `https://mmb-web.adlibhosting.com/search`
- Detail page URL pattern: `https://mmb-web.adlibhosting.com/ais6/Details/collect/{priref}`
- Image URL pattern: `https://mmb-web.adlibhosting.com/ais6/webapi/wwwopac.ashx?command=getcontent&server=images&value={filename}&folderId=2&width=800&height=800&imageformat=jpg`
- Observed total records: ~83,758

The abbreviation leaves room for a future `rhbb` source for the book collection database.

## Files

```text
pipeline/sources/museums/rbhc/
  fetcher.py
  loader.py
  mapper.py

docs/sample_config/rbhc.json
harvest-rbhc.py
harvest-rbhc.sh
tests/test_rbhc_pipeline.py
tests/test_rbhc-record.sh
tests/fixtures/rbhc-record-2.json
```

## Config

Set up the runtime config once — the pipeline reads all JSON configs
from `{LUX_BASEPATH}/config_cache/` (top level, next to `manage-data.py`):

```bash
mkdir -p config_cache && cp docs/sample_config/*.json config_cache/
```

## Run

```bash
cd data-pipeline

./harvest-rbhc.sh
uv run --python 3.12 --with-requirements requirements.txt python manage-data.py --load --rbhc
uv run --python 3.12 --with-requirements requirements.txt python run-reconcile.py 0 1 --rbhc
uv run --python 3.12 --with-requirements requirements.txt python run-merge.py 0 1 --rbhc
uv run --python 3.12 --with-requirements requirements.txt python run-export.py 0 1 --rbhc --export-entities
```

Validate a loaded test record from bash:

```bash
./tests/test_rbhc-record.sh 2
```

`harvest-rbhc.sh` runs both the bulk harvest and the required per-record enrichment. For a quick single-record test, enrich only the test record before loading:

```bash
uv run --python 3.12 --with-requirements requirements.txt python enrich-rbhc.py data/input/rbhc 2
```

## Carousel

The rbhc source has a named carousel collection
(`caroussel/config/default.json`):

- URL: `http://localhost:8089/?collection=rbhc`
- Label: Rijksmuseum Boerhaave
- URI prefix: `https://mmb-web.adlibhosting.com/ais6/Details/collect/`
- Credit line: Rijksmuseum Boerhaave, Leiden

Re-running `./harvest-rbhc.sh` re-fetches and rewrites existing files (no
skip-if-exists). Export slice files are overwritten in `"w"` mode and
`manage-data.py --load --rbhc` clears the rbhc datacache first, so
downstream cleanup is never needed.

Load records with images and titles under the URI prefix into the backend
DB (upserts by URI, no reset needed):

```bash
cd backend
uv run --python 3.12 --with-requirements requirements.txt \
    python scripts/load_data.py ../data-pipeline/data/output/latest/
```

Until its records are loaded, `?collection=rbhc` returns a "no objects yet"
message naming the collection.
