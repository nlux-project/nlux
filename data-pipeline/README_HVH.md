# Huis van Hilde Source

Integration of the Huis van Hilde / Provinciaal Depot voor Archeologie Noord-Holland collection into the NLUX data pipeline.

## Harvesting

The source exposes an OAI-PMH endpoint with `metadataPrefix=oai_pnh`:

```text
http://62.221.199.184:17518/oai
```

Relevant verbs:

- `ListIdentifiers`: full identifier listing with `resumptionToken` paging
- `GetRecord`: record fetch by identifier, for example `5061-06`

Source landing page:

- `https://collectie.huisvanhilde.nl/oaidata.aspx`

As observed on April 24, 2026, the OAI feed reported `completeListSize="18423"`.

## Files

```text
pipeline/sources/museums/hvh/
  fetcher.py
  harvester.py
  loader.py
  mapper.py
  parser.py

docs/sample_config/hvh.json
harvest-hvh.py
harvest-hvh.sh
tests/test_hvh_pipeline.py
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

./harvest-hvh.sh
uv run --python 3.12 --with-requirements requirements.txt python manage-data.py --load --hvh
uv run --python 3.12 --with-requirements requirements.txt python run-reconcile.py 0 1 --hvh
uv run --python 3.12 --with-requirements requirements.txt python run-merge.py 0 1 --hvh
uv run --python 3.12 --with-requirements requirements.txt python run-export.py 0 1 --hvh
```

The last three steps need PostgreSQL + Redis (`docker compose --profile pipeline up`)
and the AAT reconciliation index built once
(`uv run --python 3.12 --with-requirements requirements.txt python run-harvest.py --aat` + `uv run --python 3.12 --with-requirements requirements.txt python manage-data.py --load-index --aat`).

## Re-harvesting

The harvester is skip-if-exists: re-running `./harvest-hvh.sh` only fetches
identifiers whose `data/input/hvh/{identifier}.json` does not exist yet —
records that changed upstream stay stale. To refresh changed records too,
move the old harvest aside first (the harvester recreates the directory):

```bash
mv data/input/hvh data/input/hvh-old-$(date +%Y%m%d)
./harvest-hvh.sh
```

Downstream cleanup is never needed:

- `manage-data.py --load --hvh` clears the hvh datacache before loading
  (idempotent)
- `run-export.py` opens `export_hvh_0.jsonl` in `"w"` mode, so each export
  run overwrites it
- after a re-harvest, re-run reconcile + merge so the idmap merge decisions
  pick up the new records

## Carousel

The hvh source has a named carousel collection
(`caroussel/config/default.json`):

- URL: `http://localhost:8089/?collection=hvh`
- Label: Huis van Hilde
- URI prefix: `https://collectie.huisvanhilde.nl/resource/`
- Credit line: Huis van Hilde, Castricum

Load route into the carousel backend DB (upserts by URI, no reset
needed) — from raw harvest files via the mapper, which mints URIs under
the namespace above (pipeline exports use different ids and will not
match the collection's URI prefix):

```bash
make carousel-load-hvh             # 400 image+title objects
# knobs: CAROUSEL_HVH_COUNT / CAROUSEL_HVH_SEED
```

Of the 19,514 raw records, 19,047 have an image and a title, so larger
`CAROUSEL_HVH_COUNT` values work fine.
