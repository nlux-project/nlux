#!/bin/bash
set -euo pipefail

OUTPUT_DIR="${1:-data/input/fhm}"
LIMIT="${2:-}"

mkdir -p "$OUTPUT_DIR"
if [ -n "$LIMIT" ]; then
    uv run python harvest-fhm.py "$OUTPUT_DIR" "$LIMIT"
else
    uv run python harvest-fhm.py "$OUTPUT_DIR"
fi
