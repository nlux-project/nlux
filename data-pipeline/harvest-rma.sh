#!/bin/bash
set -euo pipefail

OUTPUT_DIR="${1:-data/input/rma}"
LIMIT="${2:-}"

if [[ -n "$LIMIT" ]]; then
    uv run --python 3.12 --with-requirements requirements.txt python harvest-rma.py "$OUTPUT_DIR" "$LIMIT"
else
    uv run --python 3.12 --with-requirements requirements.txt python harvest-rma.py "$OUTPUT_DIR"
fi

#uv run --python 3.12 --with-requirements requirements.txt python enrich-rma.py "$OUTPUT_DIR"

# load into postgresql
uv run --python 3.12 --with-requirements requirements.txt python manage-data.py --load --rma

uv run --python 3.12 --with-requirements requirements.txt python ./run-reconcile.py 0 1 --rma
uv run --python 3.12 --with-requirements requirements.txt python ./run-merge.py 0 1 --rma
uv run --python 3.12 --with-requirements requirements.txt python ./run-export.py 0 1 --rma

# load into SQLite (DEV only) — fills the API database (backend/nlux.db), run from the repo root:
# uv run --python 3.12 --with-requirements backend/requirements.txt \
#     python backend/scripts/load_data.py data-pipeline/output/latest/
