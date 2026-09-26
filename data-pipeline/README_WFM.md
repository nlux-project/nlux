# Westfries Museum Source (WFM)

Integration of the Westfries Museum online beeldbank into the NLUX data pipeline.

## Harvesting

The public collection page embeds the Memorix mediabank widget:

```text
https://westfriesmuseum.com/?mode=gallery
```

The page exposes the public API configuration used by the harvester:

```text
API base: https://webservices.memorix.nl/mediabank
API key:  0f18ed8a-b243-11e6-94c8-9f49a90dcd1d
```

- Source abbreviation: `wfm`
- Detail page URL pattern: `https://westfriesmuseum.com/detail/{record_id}`
- Image host: `https://images.memorix.nl/wfm/`
- Observed total records: 5,428

## Files

```text
pipeline/sources/museums/wfm/
  fetcher.py
  loader.py
  mapper.py

docs/sample_config/wfm.json
harvest-wfm.py
harvest-wfm.sh
re-harvest-wfm.sh
tests/test_wfm_pipeline.py
tests/fixtures/wfm-record-c396d24a.json
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

./harvest-wfm.sh
uv run --python 3.12 --with-requirements requirements.txt python manage-data.py --load --wfm
uv run --python 3.12 --with-requirements requirements.txt python run-reconcile.py 0 1 --wfm
uv run --python 3.12 --with-requirements requirements.txt python run-merge.py 0 1 --wfm
uv run --python 3.12 --with-requirements requirements.txt python run-export.py 0 1 --wfm --export-entities
```

For a small harvest smoke test:

```bash
./harvest-wfm.sh data/input/wfm 10
```

For the full local rebuild and Docker API reload:

```bash
./re-harvest-wfm.sh
```

## Carousel

The wfm source has a named carousel collection
(`caroussel/config/default.json`):

- URL: `http://localhost:8089/?collection=wfm`
- Label: Westfries Museum
- URI prefix: `https://westfriesmuseum.com/detail/`
- Credit line: Westfries Museum, Hoorn

Re-running `./harvest-wfm.sh` re-fetches and rewrites existing files (no
skip-if-exists). Export slice files are overwritten in `"w"` mode and
`manage-data.py --load --wfm` clears the wfm datacache first, so
downstream cleanup is never needed.

Load route into the carousel backend DB (upserts by URI, no reset
needed) — from raw harvest files via the mapper, which mints URIs under
the namespace above (pipeline exports use different ids and will not
match the collection's URI prefix):

```bash
make carousel-load-wfm             # 400 image+title objects
# knobs: CAROUSEL_WFM_COUNT / CAROUSEL_WFM_SEED
```

Of the 5,433 raw records, 5,179 have an image and a title, so larger
`CAROUSEL_WFM_COUNT` values work fine. Images are served from
images.memorix.nl, already in the backend's trusted image hosts.

Until its records are loaded, `?collection=wfm` returns a "no objects yet"
message naming the collection.
