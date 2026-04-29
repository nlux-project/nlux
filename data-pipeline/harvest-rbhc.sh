#!/bin/bash
set -euo pipefail

OUTPUT_DIR="${1:-data/input/rbhc}"
mkdir -p "$OUTPUT_DIR"
uv run python harvest-rbhc.py "$OUTPUT_DIR"
