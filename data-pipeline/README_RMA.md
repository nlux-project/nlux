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
uv run python manage-data.py --load --rma
uv run python run-reconcile.py 0 1 --rma
uv run python run-merge.py 0 1 --rma
uv run python run-export.py 0 1 --rma --export-entities
```

For a small harvest smoke test:

```bash
./harvest-rma.sh data/input/rma 10
```
