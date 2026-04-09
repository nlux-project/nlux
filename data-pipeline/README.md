# Teylers Museum Source

Integration of the [Teylers Museum](https://www.teylersmuseum.nl) collection into the data pipeline.

## API

Data is fetched from the Axiell AIS6 Adlib webapi:

```
https://teylers.adlibhosting.com/ais6/webapi/wwwopac.ashx
```

- **Database name:** `museum`
- **Total records:** ~100,685
- **Output format:** Adlib grouped JSON (`xmltype=Grouped`)
- **Detail page URL pattern:** `https://teylers.adlibhosting.com/ais6/Details/museum/{priref}`
- **Image URL pattern:** `https://teylers.adlibhosting.com/ais6/Content/GetContent?command=getcontent&server=images&value={filename}&folderId=1&width=800&height=800&imageformat=jpg`

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
harvest-teylers.py                 # standalone harvest script
harvest-teylers.sh                 # wrapper shell script
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

### 1. Harvest raw records to disk

```bash
./harvest-teylers.sh
# or with a custom output directory:
./harvest-teylers.sh /path/to/output
```

Writes `data/input/teylers/{priref}.json` — one file per record. Re-running is safe; existing files are skipped.

### 2. Full pipeline

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

### 3. Optional: load authority data for cross-source reconciliation

Without authority data the pipeline still works, but AAT type URIs and the Wikidata `current_owner` reference will not be enriched or linked across sources. "Failed to acquire" warnings during reconcile are expected in this case.

#### AAT (Getty Art & Architecture Thesaurus)

Harvests live from Getty's activity stream — no download needed:

```bash
# Harvest AAT records from Getty's API
uv run python ./run-harvest.py --aat

# Build the reconciliation index (label → AAT id lookup)
uv run python ./manage-data.py --load-index --aat

# Re-reconcile teylers now that AAT is available
uv run python ./run-reconcile.py 0 1 --teylers
```

#### Wikidata

Requires the full dump (~100 GB compressed). Only needed if you want to link creators and places across sources.

```bash
# Download the dump (takes hours)
mkdir -p data/input/wikidata
curl -L https://dumps.wikimedia.org/wikidatawiki/entities/latest-all.json.gz \
    -o data/input/wikidata/latest-all.json.gz

# Load into the datacache (parallel, 24 slices)
./load_parallel.sh --wikidata

# Build the reconciliation index
uv run python ./manage-data.py --load-index --wikidata
```

**Recommendation:** Start with AAT only. It is fast, covers all the type classifications Teylers records reference, and requires no large download. Wikidata is only worth loading if you need to reconcile creators and places against other sources.

## Known issues / dependencies

- Requires **Python 3.9** with `pyld<2.0.2` (pyld 2.0.2+ uses `str | None` syntax incompatible with Python 3.9).
- Requires PostgreSQL and Redis to be running before any pipeline phase (`manage-data`, `run-reconcile`, `run-merge`, `run-export`).
- The harvest script (`harvest-teylers.sh`) only requires network access — no database needed.
