# Teylers Museum Source

Integration of the [Teylers Museum](https://www.teylersmuseum.nl) collection into the data pipeline.

## API

Data is fetched from the Axiell AIS6 Adlib webapi:

```
https://teylers.adlibhosting.com/ais6/webapi/wwwopac.ashx
```

- **Database name:** `museum`
- **Total records:** ~100,685
- **Output format:** Adlib grouped JSON
- **Detail page URL pattern:** `https://teylers.adlibhosting.com/ais6/Details/museum/{priref}`
- **Image URL pattern:** `https://teylers.adlibhosting.com/ais6/Content/GetContent?command=getcontent&server=images&value={filename}&folderId=1&width=800&height=800&imageformat=jpg`

**Note:** The Adlib `search=all` bulk endpoint returns a reduced field set (Title, Production, Dating, Object_name, Media, object_number). Fields like `Dimension`, `Material`, `Technique`, and `Content_subject` are only available when fetching records individually by priref. The enrichment step handles this (see below).

## Source files

```
pipeline/sources/museums/teylers/
  __init__.py
  mapper.py     # transforms Adlib JSON → LUX / Linked Art (CIDOC-CRM via cromulent)
  loader.py     # pages through the API and stores records in the PostgreSQL datacache
  fetcher.py    # fetches a single record by priref
```

```
config/config_cache/teylers.json   # pipeline source config
harvest-teylers.py                 # standalone bulk harvest script
harvest-teylers.sh                 # wrapper shell script
enrich-teylers.py                  # re-fetches each record individually to fill missing fields
re-harvest-teylers.sh              # full pipeline: harvest + enrich + load + reconcile + merge + export + Docker reload
```

## Configuration

`config/config_cache/teylers.json`:

```json
{
    "name": "teylers",
    "type": "internal",
    "namespace": "https://teylers.adlibhosting.com/ais6/Details/museum/",
    "matches": ["teylers.adlibhosting.com/ais6/Details/museum/"],
    "merge_order": 1,
    "harvesterClass": "process.base.harvester.Harvester",
    "mapperClass": "sources.museums.teylers.mapper.TeylersMapper",
    "loaderClass": "sources.museums.teylers.loader.TeylersLoader",
    "fetcherClass": "sources.museums.teylers.fetcher.TeylersFetcher",
    "totalRecords": 100685
}
```

## LUX / Linked Art compliance

The mapper outputs records compliant with the [LUX HumanMadeObject model](https://github.com/nlux-project/documentation/tree/main). Fields mapped:

| LUX field | Source field |
|---|---|
| `_label` | First title |
| `identified_by > Name` | `title` (primary + alternates) |
| `identified_by > Identifier` | `object_number` (accession number) |
| `classified_as` | `object_name` → AAT URI (see table below) |
| `produced_by > carried_out_by` | `creator` |
| `produced_by > timespan` | `dating.date.start` / `dating.date.end` |
| `produced_by > technique` | `technique` |
| `made_of` | `material` |
| `dimension` | `dimension.value` / `dimension.unit` / `dimension.type` |
| `current_owner` | Teylers Museum (Wikidata Q751582) |
| `subject_of` | Detail page URL |
| `representation` | First public image from `media.reference` |

### Object type → AAT mapping

| Dutch term | AAT URI | Label |
|---|---|---|
| schilderij | aat:300033618 | paintings (visual works) |
| tekening | aat:300033973 | drawings (visual works) |
| prent | aat:300041273 | prints (visual works) |
| aquarel | aat:300078925 | watercolors (paintings) |
| gouache | aat:300015017 | gouaches (paintings) |
| sculptuur / beeld | aat:300047090 | sculpture (visual works) |
| fossiel | aat:300380921 | fossils |
| instrument | aat:300266639 | scientific instruments |
| munt | aat:300037222 | coins (money) |
| penning | aat:300435429 | medals (coins) |
| boek | aat:300028051 | books |
| manuscript | aat:300028569 | manuscripts (documents) |

## Running

### Quick start: full re-harvest

The `re-harvest-teylers.sh` script runs the entire pipeline end-to-end with per-step validation:

```bash
./re-harvest-teylers.sh          # uses priref=41634 as test record
./re-harvest-teylers.sh 1        # use a different test record
```

Steps executed:
1. Bulk harvest from Adlib API (`harvest-teylers.sh`)
2. Enrich records with missing fields via individual API lookups (`enrich-teylers.py`)
3. Load into PostgreSQL datacache (`manage-data.py --load --teylers`)
4. Reconcile against AAT (`run-reconcile.py`)
5. Merge (`run-merge.py`)
6. Export to Linked Art JSONL (`run-export.py`)
7. Reset and reload Docker API database + generate agent records

Each step validates the test record and stops on first failure.

### Manual: step by step

#### 1. Harvest raw records to disk

```bash
./harvest-teylers.sh
```

Writes `data/input/teylers/{priref}.json` — one file per record. Re-running is safe; existing files are skipped.

**Important:** The bulk harvest uses `search=all` which omits `Dimension`, `Material`, `Technique`, and `Content_subject`. Run the enrichment step to fill these in:

```bash
uv run python enrich-teylers.py
```

This re-fetches each record individually (10 concurrent threads, ~20 min for 100k records) and merges the missing fields into the existing files.

#### 2. Full pipeline

```bash
# Load harvested files into the PostgreSQL datacache
python ./manage-data.py --load --teylers

# Reconcile against external authority sources
python ./run-reconcile.py 0 1 --teylers

# Merge
python ./run-merge.py 0 1 --teylers

# Export to LUX-formatted JSONL
python ./run-export.py 0 1
```

Output lands in `data/output/latest/`.

#### 3. Load into nlux API (Docker)

```bash
docker cp data/output/latest/export_full_0.jsonl nlux-api-1:/tmp/export_full_0.jsonl
docker exec nlux-api-1 python3 scripts/reset.py
docker exec nlux-api-1 python3 scripts/load_data.py /tmp/
docker exec nlux-api-1 python3 scripts/generate_agents.py
```

### AAT authority data (run once)

Without AAT the pipeline still works, but type URIs will not be enriched. "Failed to acquire" warnings during reconcile are expected without AAT.

```bash
# Harvest AAT records from Getty's API
uv run python ./run-harvest.py --aat

# Build the reconciliation index (label → AAT id lookup)
uv run python ./manage-data.py --load-index --aat

# Re-reconcile teylers now that AAT is available
uv run python ./run-reconcile.py 0 1 --teylers
```

### Wikidata (optional)

Requires the full dump (~100 GB compressed). Only needed if you want to link creators and places across sources.

```bash
mkdir -p data/input/wikidata
curl -L https://dumps.wikimedia.org/wikidatawiki/entities/latest-all.json.gz \
    -o data/input/wikidata/latest-all.json.gz

./load_parallel.sh --wikidata
uv run python ./manage-data.py --load-index --wikidata
```

**Recommendation:** Start with AAT only. It is fast, covers all the type classifications Teylers records reference, and requires no large download.

## Testing

### Per-step validation

Test scripts in `data/tests/` (or `tests/` in the git repo) validate a single record through each pipeline stage:

| Script | Validates |
|---|---|
| `test-harvest-teylers-step1.sh` | Harvest file: required fields present |
| `test-harvest-teylers-step3.sh` | PostgreSQL datacache: fields carried through |
| `test-harvest-teylers-step5.sh` | Rewritten cache after merge: Linked Art fields present |
| `test-harvest-teylers-step6.sh` | Export JSONL: Linked Art fields present |
| `test-harvest-teylers-step7.sh` | API response: all fields + HAL links + agent URIs |

All tests treat absent fields as errors (exit 1). Run individually:

```bash
./data/tests/test-harvest-teylers-step1.sh 41634
```

Or use `test-record.sh` to run all steps at once without re-running the pipeline:

```bash
./test-record.sh 41634
```

## Known issues / dependencies

- Requires **Python 3.9** with `pyld<2.0.2` (pyld 2.0.2+ uses `str | None` syntax incompatible with Python 3.9).
- Requires PostgreSQL and Redis to be running before any pipeline phase (`manage-data`, `run-reconcile`, `run-merge`, `run-export`).
- The harvest script (`harvest-teylers.sh`) only requires network access — no database needed.
- The Adlib `search=all` bulk endpoint returns a reduced field set; `enrich-teylers.py` compensates by re-fetching individually.
