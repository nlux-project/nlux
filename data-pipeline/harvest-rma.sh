#!/bin/bash
set -euo pipefail

OUTPUT_DIR="${1:-data/input/rma}"
LIMIT="${2:-}"

if [[ -n "$LIMIT" ]]; then
    uv run --python 3.12 --with-requirements requirements.txt python harvest-rma.py "$OUTPUT_DIR" "$LIMIT"
else
    uv run --python 3.12 --with-requirements requirements.txt python harvest-rma.py "$OUTPUT_DIR"
fi
