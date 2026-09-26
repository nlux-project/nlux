#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="${1:-$SCRIPT_DIR/data/input/hvh}"

mkdir -p "$OUTPUT_DIR"
cd "$SCRIPT_DIR"

#uv run --python 3.12 --with-requirements requirements.txt python enrich-hvh.py "$OUTPUT_DIR"

uv run --python 3.12 --with-requirements requirements.txt python harvest-hvh.py "$OUTPUT_DIR"
uv run --python 3.12 --with-requirements requirements.txt python manage-data.py --load --hvh
uv run --python 3.12 --with-requirements requirements.txt python ./run-reconcile.py 0 1 --hvh
uv run --python 3.12 --with-requirements requirements.txt python ./run-merge.py 0 1 --hvh
uv run --python 3.12 --with-requirements requirements.txt python ./run-export.py 0 1 --hvh
