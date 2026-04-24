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

Copy `docs/sample_config/hvh.json` into your runtime `config/config_cache/` alongside the other source configs.

## Run

```bash
cd data-pipeline
./harvest-hvh.sh
uv run python manage-data.py --load --hvh
```
