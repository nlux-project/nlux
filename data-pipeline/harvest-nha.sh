#!/bin/bash
set -euo pipefail

SOURCE="${1:-all}"
OUTPUT_DIR="${2:-}"
LIMIT="${3:-}"

if [[ "$SOURCE" == "c587" || "$SOURCE" == "587" ]]; then
    SOURCE="nha-c587"
elif [[ "$SOURCE" == "c480" || "$SOURCE" == "480" ]]; then
    SOURCE="nha-c480"
fi

if [[ "$SOURCE" != nha-* && "$SOURCE" != "all" ]]; then
    OUTPUT_DIR="$SOURCE"
    SOURCE="nha-c587"
    LIMIT="${2:-}"
fi

run_source() {
    local source="$1"
    local output_dir="$2"
    local limit="$3"

    if [[ -n "$output_dir" ]]; then
        mkdir -p "$output_dir"
    fi
    if [[ -n "$limit" ]]; then
        uv run python harvest-nha.py "$source" "$output_dir" "$limit"
    elif [[ -n "$output_dir" ]]; then
        uv run python harvest-nha.py "$source" "$output_dir"
    else
        uv run python harvest-nha.py "$source"
    fi
}

if [[ "$SOURCE" == "all" ]]; then
    run_source "nha-c587" "" "$LIMIT"
    run_source "nha-c480" "" "$LIMIT"
else
    run_source "$SOURCE" "$OUTPUT_DIR" "$LIMIT"
fi
