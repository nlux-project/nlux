#!/bin/bash
set -euo pipefail

OUTPUT_DIR="${1:-data/input/nha/c587}"
LIMIT="${2:-}"

mkdir -p "$OUTPUT_DIR"
if [ -n "$LIMIT" ]; then
    uv run python harvest-nha.py "$OUTPUT_DIR" "$LIMIT"
else
    uv run python harvest-nha.py "$OUTPUT_DIR"
fi
