# Frans Hals Museum Source (FHM)

Integration of the Frans Hals Museum online collection into the NLUX data pipeline.

## Harvesting

The source uses the public CollectionConnection endpoint behind:

```text
https://collectie.franshalsmuseum.nl/
```

The collection page posts search specifications to:

```text
https://collectie.franshalsmuseum.nl/cc/ccConnector.asmx/search
```

- Source abbreviation: `fhm`
- Public collection page: `https://collectie.franshalsmuseum.nl/`
- Detail page URL pattern: `http://collectie.franshalsmuseum.nl/?query=search=objectid={objectid}&showtype=record`
- Observed total records: ~10,986

Unlike Teylers and RBHC, this is not an Adlib JSON WebAPI. The harvester asks the CollectionConnection search endpoint for record view HTML and normalizes the rendered fields into JSON before loading.

## Files

```text
pipeline/sources/museums/fhm/
  fetcher.py
  loader.py
  mapper.py
  parser.py

docs/sample_config/fhm.json
harvest-fhm.py
harvest-fhm.sh
tests/test_fhm_pipeline.py
tests/test_fhm-record.sh
tests/fixtures/fhm-record-3.json
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

./harvest-fhm.sh
uv run --python 3.12 --with-requirements requirements.txt python manage-data.py --load --fhm
uv run --python 3.12 --with-requirements requirements.txt python run-reconcile.py 0 1 --fhm
uv run --python 3.12 --with-requirements requirements.txt python run-merge.py 0 1 --fhm
uv run --python 3.12 --with-requirements requirements.txt python run-export.py 0 1 --fhm --export-entities
```

For a small harvest smoke test:

```bash
./harvest-fhm.sh data/input/fhm 10
```

Validate a loaded test record from bash:

```bash
./tests/test_fhm-record.sh 3
```

## Carousel

The fhm source has a named carousel collection
(`caroussel/config/default.json`):

- URL: `http://localhost:8089/?collection=fhm`
- Label: Frans Hals Museum
- URI prefix: `http://collectie.franshalsmuseum.nl/?query=search=objectid=`
- Credit line: Frans Hals Museum, Haarlem

Unlike hvh/teylers, re-running `./harvest-fhm.sh` re-fetches and rewrites
existing files (no skip-if-exists). Export slice files are overwritten in
`"w"` mode and `manage-data.py --load --fhm` clears the fhm datacache
first, so downstream cleanup is never needed.

Load route into the carousel backend DB (upserts by URI, no reset
needed) — from raw harvest files via the mapper, which mints URIs under
the namespace above (pipeline exports use different ids and will not
match the collection's URI prefix):

```bash
make carousel-load-fhm             # 400 image+title objects
# knobs: CAROUSEL_FHM_COUNT / CAROUSEL_FHM_SEED
```

All 10,996 raw fhm records have an image and a title, so larger
`CAROUSEL_FHM_COUNT` values work fine. The harvester captures deep-zoom
(DZI) descriptors; the loader rewrites them to plain jpeg URLs
(`.dzi` → `.jpg&width=1200`), which the FHM image proxy serves directly.
Until its records are loaded, `?collection=fhm` returns a "no objects yet"
message naming the collection.
