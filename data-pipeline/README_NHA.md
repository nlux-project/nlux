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
- Harvest input directory: `data/input/nha/c587/`
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
tests/test_nha_pipeline.py
tests/fixtures/nha-c587-record-F7DDF7.json
```

### Config

Copy `docs/sample_config/nha-c587.json` into your runtime `config/config_cache/` alongside the other source configs.

### Run

```bash
cd data-pipeline

./harvest-nha.sh nha-c587
uv run python manage-data.py --load --nha-c587
uv run python run-reconcile.py 0 1 --nha-c587
uv run python run-merge.py 0 1 --nha-c587
uv run python run-export.py 0 1 --nha-c587 --export-entities
```

For a small harvest smoke test:

```bash
./harvest-nha.sh data/input/nha/c587 10
```

## C480 - Historieprenten Provinciale Atlas Noord-Holland

Collection 480 contains history prints from the Provinciale Atlas Noord-Holland.

### Harvesting

The public collection page embeds the Memorix mediabank widget:

```text
https://noord-hollandsarchief.nl/beelden/beeldbank/?mode=gallery&fq[]=search_s_collectie:"480 - historieprenten van de Provinciale Atlas Noord-Holland, Collectie van"
```

The source uses the same public API configuration as C587 with a different collection filter:

```text
API base: https://webservices.memorix.nl/mediabank
API key:  81749016-5b7f-4e2f-a7b7-bba1be25f33f
Filter:   search_s_collectie:"480 - historieprenten van de Provinciale Atlas Noord-Holland, Collectie van"
```

- Source abbreviation: `nha-c480`
- Source namespace: `https://hdl.handle.net/21.12102/`
- Harvest input directory: `data/input/nha/c480/`
- Image host: `https://images.memorix.nl/ranh/`
- Observed total records: 1256

### Files

```text
pipeline/sources/museums/nha/c480/
  fetcher.py
  loader.py
  mapper.py

docs/sample_config/nha-c480.json
harvest-nha.py
harvest-nha.sh
tests/test_nha_pipeline.py
tests/fixtures/nha-c480-record-65B76D.json
```

### Config

Copy `docs/sample_config/nha-c480.json` into your runtime `config/config_cache/` alongside the other source configs.

### Run

```bash
cd data-pipeline

./harvest-nha.sh nha-c480
uv run python manage-data.py --load --nha-c480
uv run python run-reconcile.py 0 1 --nha-c480
uv run python run-merge.py 0 1 --nha-c480
uv run python run-export.py 0 1 --nha-c480 --export-entities
```

Bare `./harvest-nha.sh` harvests `nha-c587`, `nha-c480`, and `nha-c1477`.

For a small harvest smoke test:

```bash
./harvest-nha.sh nha-c480 data/input/nha/c480 10
```

## C1477 - Prenten van C.G. Voorhelm Schneevoogt te Haarlem

Collection 1477 contains prints from the C.G. Voorhelm Schneevoogt collection in Haarlem.

### Harvesting

The source uses the same public API configuration as C587 and C480 with a different collection filter:

```text
API base: https://webservices.memorix.nl/mediabank
API key:  81749016-5b7f-4e2f-a7b7-bba1be25f33f
Filter:   search_s_collectie:"1477 - prenten van C.G. Voorhelm Schneevoogt te Haarlem, Collectie van"
```

- Source abbreviation: `nha-c1477`
- Source namespace: `https://hdl.handle.net/21.12102/`
- Harvest input directory: `data/input/nha/c1477/`
- Image host: `https://images.memorix.nl/ranh/`
- Collection label: `1477 - prenten van C.G. Voorhelm Schneevoogt te Haarlem`

### Files

```text
pipeline/sources/museums/nha/c1477/
  fetcher.py
  loader.py
  mapper.py

docs/sample_config/nha-c1477.json
harvest-nha.py
harvest-nha.sh
tests/test_nha_pipeline.py
```

### Config

Copy `docs/sample_config/nha-c1477.json` into your runtime `config/config_cache/` alongside the other source configs.

### Run

```bash
cd data-pipeline

./harvest-nha.sh nha-c1477
uv run python manage-data.py --load --nha-c1477
uv run python run-reconcile.py 0 1 --nha-c1477
uv run python run-merge.py 0 1 --nha-c1477
uv run python run-export.py 0 1 --nha-c1477 --export-entities
```

Bare `./harvest-nha.sh` harvests `nha-c587`, `nha-c480`, and `nha-c1477`.

For a small harvest smoke test:

```bash
./harvest-nha.sh nha-c1477 data/input/nha/c1477 10
```
