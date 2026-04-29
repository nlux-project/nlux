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

Copy `docs/sample_config/rbhc.json` into your runtime `config/config_cache/` alongside the other source configs.

## Run

```bash
cd data-pipeline

./harvest-rbhc.sh
uv run python manage-data.py --load --rbhc
uv run python run-reconcile.py 0 1 --rbhc
uv run python run-merge.py 0 1 --rbhc
uv run python run-export.py 0 1 --export-entities
```

Validate a loaded test record from bash:

```bash
./tests/test_rbhc-record.sh 2
```

`harvest-rbhc.sh` runs both the bulk harvest and the required per-record enrichment. For a quick single-record test, enrich only the test record before loading:

```bash
uv run python enrich-rbhc.py data/input/rbhc 2
```
