#!/bin/sh
set -eu

API_BASE="${API_BASE:-http://localhost:8000}"
OUTPUT_JSONL="${OUTPUT_JSONL:-/Users/lux/data-pipeline/data/output/ai-enrichment/results.jsonl}"
REPORTS_DIR="${REPORTS_DIR:-/Users/lux/data-pipeline/data/output/ai-enrichment/reports}"

if [ "${NLUX_AI_ENRICH_ENDPOINT:-}" = "$API_BASE" ]; then
  echo "NLUX_AI_ENRICH_ENDPOINT points at the NLUX data API ($API_BASE), not an AI provider." >&2
  echo "Unset it for --dry-run, or set it to the actual AI provider endpoint." >&2
  exit 1
fi

if [ -z "${NLUX_AI_ENRICH_ENDPOINT:-}" ]; then
  echo "NLUX_AI_ENRICH_ENDPOINT is not set; running prompt/API plumbing in --dry-run mode." >&2
  uv run python ai-enrichment.py objects.txt \
    --api-base "$API_BASE" \
    --output-jsonl "$OUTPUT_JSONL" \
    --reports-dir "$REPORTS_DIR" \
    --dry-run \
    --no-mark-done
else
  uv run python ai-enrichment.py objects.txt \
    --api-base "$API_BASE" \
    --output-jsonl "$OUTPUT_JSONL" \
    --reports-dir "$REPORTS_DIR"
fi
