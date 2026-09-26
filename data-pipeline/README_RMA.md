# Rijksmuseum Amsterdam Source

Integration notes for the Rijksmuseum Amsterdam collection source in the NLUX data pipeline.

The source uses the current Rijksmuseum Data Services APIs:

```text
Search API:   https://data.rijksmuseum.nl/search/collection
Resolver API: https://id.rijksmuseum.nl/{identifier}?_profile=la&_mediatype=application/ld+json
```

The Search API returns Linked Art Search result ids. Each id is resolved to Rijksmuseum Linked Art JSON and stored as harvested input.

- Source abbreviation: `rma`
- Source namespace: `https://id.rijksmuseum.nl/`
- Harvest input directory: `data/input/rma/`
- Collection label: `Rijksmuseum Amsterdam`

## Files

```text
pipeline/sources/museums/rma/
  fetcher.py
  loader.py
  mapper.py

docs/sample_config/rma.json
harvest-rma.py
harvest-rma.sh
tests/test_rma_pipeline.py
```

## Config

Copy `docs/sample_config/rma.json` into your runtime `config/config_cache/` alongside the other source configs.

## Run

```bash
cd data-pipeline

./harvest-rma.sh
uv run --python 3.12 --with-requirements requirements.txt python manage-data.py --load --rma
uv run --python 3.12 --with-requirements requirements.txt python run-reconcile.py 0 1 --rma
uv run --python 3.12 --with-requirements requirements.txt python run-merge.py 0 1 --rma
uv run --python 3.12 --with-requirements requirements.txt python run-export.py 0 1 --rma --export-entities
```

For a small harvest smoke test:

```bash
./harvest-rma.sh data/input/rma 10
```

## Carousel

The rma source has a named carousel collection
(`caroussel/config/default.json`):

- URL: `http://localhost:8089/?collection=rma`
- Label: Rijksmuseum
- URI prefix: `https://id.rijksmuseum.nl/`
- Credit line: Rijksmuseum, Amsterdam

Re-running `./harvest-rma.sh` re-fetches and rewrites existing files (no
skip-if-exists). Export slice files are overwritten in `"w"` mode and
`manage-data.py --load --rma` clears the rma datacache first, so
downstream cleanup is never needed. Note: the full export is very large
(~14 GB for ~835k records); consider loading a sample.

Load records with images and titles under the URI prefix into the backend
DB (upserts by URI, no reset needed):

```bash
cd backend
uv run --python 3.12 --with-requirements requirements.txt \
    python scripts/load_data.py ../data-pipeline/data/output/latest/
```

Until its records are loaded, `?collection=rma` returns a "no objects yet"
message naming the collection.
