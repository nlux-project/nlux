#!/bin/bash
# Harvest all Teylers Museum records from the Adlib API into individual JSON files.
# Output: data/input/teylers/<priref>.json  (one file per record)
#
# Usage: ./harvest-teylers.sh [output_dir]

set -euo pipefail

OUTPUT_DIR="${1:-data/input/teylers}"
mkdir -p "$OUTPUT_DIR"

uv run --python 3.12 --with-requirements requirements.txt python harvest-teylers.py "$OUTPUT_DIR"

#uv run --python 3.12 --with-requirements requirements.txt python enrich-teylers.py "$OUTPUT_DIR"

uv run --python 3.12 --with-requirements requirements.txt python manage-data.py --load --teylers
uv run --python 3.12 --with-requirements requirements.txt python ./run-reconcile.py 0 1 --teylers
uv run --python 3.12 --with-requirements requirements.txt python ./run-merge.py 0 1 --teylers
uv run --python 3.12 --with-requirements requirements.txt python ./run-export.py 0 1 --teylers
