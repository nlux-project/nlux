# NLUX AI enrichment sidecar

This experiment generates AI research sidecars for selected NLUX object records.
The sidecar is intentionally separate from the import pipeline: it proposes
human-reviewable additions and corrections without changing catalog fields.

## Checklist input

Use a plain text file with one object per line:

```text
[ ] 05477c72-b195-413c-afc6-1473fd31d317
[X] already-processed-object-id
```

Unchecked records are fetched from `http://localhost:8000/data/object/{id}` by
default. Full API URLs are also accepted.

## Generate sidecars

```bash
python data-pipeline/experiments/ai-enrichment/ai-enrichment.py objects.txt \
  --api-base http://localhost:8000 \
  --output-jsonl data/output/ai-enrichment/results.jsonl \
  --reports-dir data/output/ai-enrichment/reports
```

Without `--dry-run`, the script calls the provider configured by
`NLUX_AI_ENRICH_ENDPOINT` and optional `NLUX_AI_ENRICH_API_KEY`. The provider
must return JSON matching `prompt.md`.

For prompt/API plumbing only:

```bash
python data-pipeline/experiments/ai-enrichment/ai-enrichment.py objects.txt --dry-run --no-mark-done
```

## Load sidecars into the API

After reviewing the generated JSONL, load successful sidecars into the API DB:

```bash
python backend/scripts/load_ai_enrichment.py data/output/ai-enrichment/results.jsonl \
  --base-uri http://localhost:8000
```

The loader appends a Linked Art `referred_to_by` note classified as
`AI Research Analysis`. The frontend already detects this note and displays it
in the object details page as a separate AI Research box.
