#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="${1:-$SCRIPT_DIR/data/input/hvh}"

mkdir -p "$OUTPUT_DIR"
cd "$SCRIPT_DIR"
uv run python harvest-hvh.py "$OUTPUT_DIR"
