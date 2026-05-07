# Noord-Hollands Archief Sources

Integration notes for Noord-Hollands Archief collections in the NLUX data pipeline. NHA sources use the public Memorix mediabank API exposed by the NHA beeldbank pages.

## C587 - Portretten Provinciale Atlas Noord-Holland

Collection 587 contains portraits from the Provinciale Atlas Noord-Holland.

### Harvesting

The public collection page embeds the Memorix mediabank widget:

```text
https://noord-hollandsarchief.nl/beelden/beeldbank/?mode=gallery&fq[]=search_s_collectie:"587 - portretten van de Provinciale Atlas Noord-Holland, Collectie van"
```

The page exposes the public API configuration used by the harvester:

```text
API base: https://webservices.memorix.nl/mediabank
API key:  81749016-5b7f-4e2f-a7b7-bba1be25f33f
Filter:   search_s_collectie:"587 - portretten van de Provinciale Atlas Noord-Holland, Collectie van"
```

- Source abbreviation: `nha-c587`
- Source namespace: `https://hdl.handle.net/21.12102/`
- Image host: `https://images.memorix.nl/ranh/`
- Observed total records: 893

### Files

```text
pipeline/sources/museums/nha/c587/
  fetcher.py
  loader.py
  mapper.py

docs/sample_config/nha-c587.json
harvest-nha.py
harvest-nha.sh
tests/test_nha_c587_pipeline.py
tests/fixtures/nha-c587-record-F7DDF7.json
```

### Config

Copy `docs/sample_config/nha-c587.json` into your runtime `config/config_cache/` alongside the other source configs.

### Run

```bash
cd data-pipeline

./harvest-nha.sh
uv run python manage-data.py --load --nha-c587
uv run python run-reconcile.py 0 1 --nha-c587
uv run python run-merge.py 0 1 --nha-c587
uv run python run-export.py 0 1 --nha-c587 --export-entities
```

For a small harvest smoke test:

```bash
./harvest-nha.sh data/input/nha-c587 10
```
