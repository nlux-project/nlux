# AI Enrichment Sidecar

AI enrichment is an optional post-export step for adding auditable research notes
to exported Linked Art JSONL records. It writes research results to a separate
JSONL sidecar first, then merges a presentation-friendly AI Research note into
exported records without changing harvested catalog fields.

## Flow

There are two supported ways to apply AI enrichment:

- **Export merge flow**: generate sidecars from exported JSONL, merge them into
  exported JSONL, then load that enriched export into the API database. Use this
  when enrichment should survive a full database reload.
- **Checklist/API flow**: load the normal export into the API database first,
  run `experiments/ai-enrichment/ai-enrichment.py` against selected object IDs
  through `localhost:8000`, review the output, then load accepted sidecars into
  the current API database with `backend/scripts/load_ai_enrichment.py`.

For the checklist/API flow, the sidecar step runs **after** the Docker/API load,
because the script fetches known data from
`http://localhost:8000/data/object/{id}`.

```text
run-export.py
  -> backend/scripts/load_data.py
  -> verify http://localhost:8000/data/object/{id}
  -> experiments/ai-enrichment/ai-enrichment.py
  -> backend/scripts/load_ai_enrichment.py
  -> frontend object detail page shows AI Research
```

Reloading the API database from normal exported JSONL later will remove
directly loaded sidecar notes. Merge sidecars into the export first when the
enrichment must be part of the reloadable dataset.

### Export Merge Flow

```text
run-export.py
  -> data/output/latest/*.jsonl
  -> run-ai-enrich.py
  -> data/output/ai-enrichment/*.jsonl
  -> merge-ai-enrichment.py
  -> data/output/latest-ai-enriched/*.jsonl
  -> backend/scripts/load_data.py
```

### Checklist/API Flow

```bash
cd data-pipeline
python experiments/ai-enrichment/ai-enrichment.py \
  experiments/ai-enrichment/objects.example.txt \
  --api-base http://localhost:8000
```

After reviewing the generated sidecar and Markdown report:

```bash
cd ..
python backend/scripts/load_ai_enrichment.py \
  data-pipeline/data/output/ai-enrichment/results.jsonl \
  --base-uri http://localhost:8000
```

## Generate Sidecar Rows

Dry run, useful for testing the resume/progress path without calling an AI
provider:

```bash
cd data-pipeline
python3 run-ai-enrich.py data/output/latest \
  --source teylers \
  --dry-run \
  --output data/output/ai-enrichment/teylers_0.jsonl \
  --progress-every 25
```

Provider-backed run:

```bash
export NLUX_AI_ENRICH_ENDPOINT="https://example.provider/enrich"
export NLUX_AI_ENRICH_API_KEY="..."

python3 run-ai-enrich.py data/output/latest \
  --source teylers \
  --model your-model-name \
  --prompt-version ai-research-v1 \
  --output data/output/ai-enrichment/teylers_0.jsonl
```

Useful options:

- `--limit 10` processes only the first 10 matching records.
- `--record-id <uri>` processes one exported record id; repeatable.
- `--slice 0 --max-slices 8` partitions records for parallel runs.
- `--force` writes new rows even if the output already contains the record.
- `--prompt <path>` uses a custom prompt template.

## Resume Behavior

`run-ai-enrich.py` is append-only and resumable by default.

On startup it reads the existing output sidecar and skips any `record_id` already
present. A restarted run reports:

```text
AI enrichment: source=teylers, slice=0/1, resume=on, existing_rows=123
Wrote 0 AI enrichment sidecar rows ... (scanned=123, resumed_skips=123, ...)
```

Use `--force` only when you intentionally want another row for records that were
already processed.

## Sidecar Format

Each JSONL row is keyed by `record_id` and includes:

```json
{
  "record_id": "https://example.org/data/object/1355",
  "source": "teylers",
  "generated_at": "2026-03-07T00:00:00Z",
  "model": "model-name",
  "prompt_version": "ai-research-v1",
  "summary": "Short research summary.",
  "catalog_snapshot": {},
  "findings": [],
  "sources": [],
  "raw_response_ref": null,
  "status": "ok"
}
```

Valid statuses are `ok`, `skipped`, and `error`. Only `ok` rows are merged into
exports. `ok` rows must include at least one source.

## Merge Into Export JSONL

```bash
python3 merge-ai-enrichment.py \
  data/output/latest \
  data/output/ai-enrichment \
  --output-dir data/output/latest-ai-enriched \
  --base-uri http://localhost:8000/
```

The merge step:

- appends one `referred_to_by` `LinguisticObject`
- classifies it as `AI Research Analysis`
- includes `_content_html` for frontend display
- is idempotent and will not duplicate the AI note on rerun
- does not modify catalog titles, identifiers, dates, places, dimensions,
  classifications, or existing notes

## Backend Search Indexing

AI Research notes are loaded with the full JSON record. They are excluded from
`search_text` by default so enrichment does not silently change discovery
behavior.

To include AI enrichment text in search:

```bash
export NLUX_INDEX_AI_ENRICHMENT=1
python backend/scripts/load_data.py data-pipeline/output/latest-ai-enriched/
```

## Frontend Display

The frontend detects the `AI Research Analysis` note and renders it in a separate
AI Research section on detail pages. The same note is filtered out of regular
Notes, keeping harvested catalog notes visually separate from AI-generated
research.

## Tests

Pipeline and merge behavior:

```bash
cd data-pipeline
PYTHONPYCACHEPREFIX=/tmp/nlux-pycache python3 -m unittest tests.test_ai_enrichment
```

Backend search-text behavior:

```bash
cd backend
PYTHONPYCACHEPREFIX=/tmp/nlux-pycache python3 -m unittest tests.test_ai_enrichment_load
```

Frontend parser/component behavior:

```bash
cd ../lux-frontend/client
npm run test -- --run -t "getAiResearch|AiResearch" EntityParser.spec.ts AiResearch.spec.tsx
```
