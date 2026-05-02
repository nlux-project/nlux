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

Copy `docs/sample_config/fhm.json` into your runtime `config/config_cache/` alongside the other source configs.

## Run

```bash
cd data-pipeline

./harvest-fhm.sh
uv run python manage-data.py --load --fhm
uv run python run-reconcile.py --fhm
uv run python run-merge.py --fhm
uv run python run-export.py 0 1 --export-entities
```

For a small harvest smoke test:

```bash
./harvest-fhm.sh data/input/fhm 10
```

Validate a loaded test record from bash:

```bash
./tests/test_fhm-record.sh 3
```
