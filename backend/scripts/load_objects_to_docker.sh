#!/usr/bin/env bash
# Load Teylers object JSON files into the Docker container DB.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
OBJECTS_DIR="$BACKEND_DIR/sample_data/teylers/objects"
CONTAINER="nlux-api-1"

docker cp "$OBJECTS_DIR" "$CONTAINER:/tmp/objects"
docker exec "$CONTAINER" python3 scripts/load_data.py /tmp/objects/
