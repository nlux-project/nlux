#!/bin/bash
set -euo pipefail

OUTPUT_DIR="${1:-data/input/fhm}"
LIMIT="${2:-}"

mkdir -p "$OUTPUT_DIR"
if [ -n "$LIMIT" ]; then
    uv run --python 3.12 --with-requirements requirements.txt python harvest-fhm.py "$OUTPUT_DIR" "$LIMIT"
else
    uv run --python 3.12 --with-requirements requirements.txt python harvest-fhm.py "$OUTPUT_DIR"
fi

#uv run --python 3.12 --with-requirements requirements.txt python enrich-fhm.py "$OUTPUT_DIR"

uv run --python 3.12 --with-requirements requirements.txt python manage-data.py --load --fhm
uv run --python 3.12 --with-requirements requirements.txt python ./run-reconcile.py 0 1 --fhm
uv run --python 3.12 --with-requirements requirements.txt python ./run-merge.py 0 1 --fhm
uv run --python 3.12 --with-requirements requirements.txt python ./run-export.py 0 1 --fhm
