# AGENTS.md

## What This Is

A Python-based ETL pipeline for reconciling, merging, and exporting linked data records from multiple institutional sources (museums, archives, libraries — Yale collections, Getty vocabularies, LC authorities, Wikidata, etc.). Records are mapped to CIDOC-CRM via the `cromulent` library, reconciled across sources, merged into unified entities, and exported as JSONL.

## Environment Setup

Requires a `.env` file (see `data/config/config_cache/example-dotenv.txt`):
```
LUX_BASEPATH="/path/to/lux/config"
```

`LUX_BASEPATH` must point to a directory that contains `data/config/config_cache/` with the JSON config files. All other paths in `base.json` are relative to this.

**Runtime dependencies:** PostgreSQL (record caches), Redis (idmap, ref maps), LMDB (alternate idmap backend), Python 3.9+ with venv at `.venv/`.

**Before running merge:** `run-merge.py` requires `data/files/idmap_update_token.txt` to exist with a token of the form `__YYYYMMDD__`. Generate it with:
```bash
python ./manage-data.py --clear-all --new-token
```

## Running the Pipeline

**Full pipeline:**
```bash
./run-all.sh --all         # full build, all sources
./full-build.sh            # hardcoded two-phase build (YPM first, then all sources)
```

**Individual phases (each supports slice parallelism):**
```bash
python ./run-reconcile.py [slice_num] [max_slices] [--all|--source <name>]
python ./run-merge.py     [slice_num] [max_slices] [--all|--source <name>]
python ./run-export.py    [slice_num] [max_slices]
python ./manage-data.py   [options]   # load/manage data; supports --load --<source>
```

All `run-*.py` scripts accept `--profile` to emit cProfile stats, and `--norefs` (reconcile/merge) to skip reference tracking.

**Parallel execution (24 slices by default):**
```bash
./reconcile_parallel.sh
./merge_parallel.sh
./export_parallel.sh
./import_parallel.sh
./load_parallel.sh
./harvest_parallel.sh
```

**Debugging:**
```bash
python ./debug-reconcile.py <from_uri> <to_uri>   # visualize reconciliation path between two records
python ./make_test_dataset.py                      # build local test dataset without writing to live data
```

## Architecture

### Data Flow
```
Sources → Load (manage-data.py) → Reconcile → Merge → Export → JSONL output
```

The full build runs two reconcile+merge passes: first for a subset (e.g. YPM), then for all sources. This is reflected in `full-build.sh`.

### Core Package (`pipeline/`)

- **`config.py`** — Central configuration system. Loads JSON configs from `data/config/config_cache/`. `base.json` defines global settings (record types, paths, `max_distance`, `internal_uri`). Per-source `{source}.json` defines mapper/loader/reconciler classes, namespace, and merge order. `caches.json` has PostgreSQL connection settings. `globals.json` maps semantic role names to AAT IDs. `map_*.json` files configure idmap, networkmap, and ref-tracking stores.

- **`process/`** — Main processing logic:
  - `reconciler.py` — Orchestrates reconciliation across all sources using per-source reconcilers + a global `GlobalReconciler` from `sources/lux/final/`
  - `merger.py` — Merges equivalent records into unified entities
  - `reidentifier.py` — Assigns new UUIDs/URIs to merged records; preserves equivalents for AAT/Wikidata globals
  - `reference_manager.py` — Tracks cross-source references and graph distances
  - `collector.py` — Collects equivalents during reconciliation
  - `update_manager.py` — Handles incremental updates
  - `validator.py` — Record validation

- **`process/base/`** — Abstract base classes for all source implementations: `mapper.py`, `loader.py`, `fetcher.py`, `acquirer.py`, `harvester.py`, `reconciler.py`, `index_loader.py`

- **`storage/`** — Pluggable backends:
  - `cache/`: PostgreSQL (`postgres.py`), Redis, filesystem
  - `idmap/`: Redis (default), memory, filesystem, LMDB — maps source URIs to internal UUIDs
  - `marklogic/`: MarkLogic XML database for final output

- **`sources/`** — Active source implementations. Currently: `lc/`, `fast/`, `getty/`, `gbif/`, `homosaurus/`, `nomisma/`, `oclc/`, and `general/` (containing `geonames/`, `orcid/`, `ror/`, `wikidata/`, `wikimedia/`, `wof/`). Each source has `mapper.py`, `loader.py`, `fetcher.py`, `reconciler.py`.

- **`sources.org/`** — Archived/reference implementations for the full original source set, organized by domain: `yale/`, `general/`, `libraries/`, `authorities/`, `archives/`, `museums/`, `lux/`. Contains `lux/final/` (GlobalReconciler, Cleaner mapper used by `merged.json`) and `lux/internal/`, `lux/marklogic/`, `lux/qlever/`.

### Config Structure (`data/config/config_cache/`)

- **`base.json`** — Global settings: `ok_record_types`, `reconcile_record_types`, path roots, `max_distance`, `internal_uri`, `do_not_reidentify` patterns
- **`caches.json`** — PostgreSQL connection (host, port, user, password, dbname)
- **`globals.json`** — Maps semantic names (e.g. `primaryName`, `nationality`) to AAT IDs; used by reidentifier to preserve AAT/Wikidata equivalents
- **`map_idmap.json`** — IdMap store config (Redis-backed by default, `prefix_map_out` controls UUID→URI mapping)
- **`merged.json`** — The merge result target: uses `MergedRecordCache`, `sources.lux.final.mapper.Cleaner`, and `sources.lux.final.reconciler.GlobalReconciler`
- **Per-source files** (e.g. `aat.json`, `wikidata.json`) — Namespace, mapper/loader/reconciler class paths, merge priority

### Data Directory Layout
```
data/
  config/config_cache/   # JSON config per source + base.json
  files/                 # sameAs/differentFrom mappings, replacements.json (Getty redirects)
    idmap_update_token.txt  # required by run-merge.py; format: __YYYYMMDD__
  input/                 # raw source dumps
  output/latest/         # JSONL export output
  processing/            # search indexes (reconcileDbPath, inverseEquivDbPath)
  logs/                  # phase logs + flags/ for completion markers
  tests/                 # test datasets
```

### Key Concepts

- **Slices**: Processing is partitioned into N slices (default 24) for parallelism. Each script accepts `[slice_num] [max_slices]`.
- **Record types**: `ok_record_types` in `base.json` maps CRM class names to short slugs (used in export URIs). Only `reconcile_record_types` participate in cross-source reconciliation.
- **Merge order**: Sources have a priority order defined in their config; higher-priority sources "win" conflicting field values during merge.
- **Status flags**: Filesystem marker files in `data/logs/flags/` track completion of each phase per slice — used by parallel scripts to skip already-completed work and by `run-all.sh` to poll for completion.
- **idmap**: Maps source-namespace URIs to internal UUIDs. Redis-backed by default; `prefix_map_out` in `map_idmap.json` controls UUID-to-URI prefix substitution on output.
- **`debug_reconciliation`**: Set `cfgs.debug_reconciliation = True` (or in `base.json`) to enable per-record reconciliation tracing and graph output.
