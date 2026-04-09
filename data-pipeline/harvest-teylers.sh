#!/bin/bash
# Harvest all Teylers Museum records from the Adlib API into individual JSON files.
# Output: data/input/teylers/<priref>.json  (one file per record)
#
# Usage: ./harvest-teylers.sh [output_dir]

set -euo pipefail

OUTPUT_DIR="${1:-data/input/teylers}"
mkdir -p "$OUTPUT_DIR"

uv run python harvest-teylers.py "$OUTPUT_DIR"
