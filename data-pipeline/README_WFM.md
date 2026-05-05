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

Copy `docs/sample_config/wfm.json` into your runtime `config/config_cache/` alongside the other source configs.

## Run

```bash
cd data-pipeline

./harvest-wfm.sh
uv run python manage-data.py --load --wfm
uv run python run-reconcile.py 0 1 --wfm
uv run python run-merge.py 0 1 --wfm
uv run python run-export.py 0 1 --biographies
```

For a small harvest smoke test:

```bash
./harvest-wfm.sh data/input/wfm 10
```

For the full local rebuild and Docker API reload:

```bash
./re-harvest-wfm.sh
```
