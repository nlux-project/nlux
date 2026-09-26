#!/bin/bash
set -euo pipefail

OUTPUT_DIR="${1:-data/input/rbhc}"
mkdir -p "$OUTPUT_DIR"
uv run --python 3.12 --with-requirements requirements.txt python harvest-rbhc.py "$OUTPUT_DIR"
uv run --python 3.12 --with-requirements requirements.txt python enrich-rbhc.py "$OUTPUT_DIR"
