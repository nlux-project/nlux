#!/bin/bash
set -euo pipefail

SOURCE="${1:-nha-c587}"
OUTPUT_DIR="${2:-}"
LIMIT="${3:-}"

if [[ "$SOURCE" != nha-* ]]; then
    OUTPUT_DIR="$SOURCE"
    SOURCE="nha-c587"
    LIMIT="${2:-}"
fi

if [[ -n "$OUTPUT_DIR" ]]; then
    mkdir -p "$OUTPUT_DIR"
fi
if [[ -n "$LIMIT" ]]; then
    uv run python harvest-nha.py "$SOURCE" "$OUTPUT_DIR" "$LIMIT"
elif [[ -n "$OUTPUT_DIR" ]]; then
    uv run python harvest-nha.py "$SOURCE" "$OUTPUT_DIR"
else
    uv run python harvest-nha.py "$SOURCE"
fi
