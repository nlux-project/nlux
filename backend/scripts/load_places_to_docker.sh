#!/usr/bin/env bash
# Generate Place JSON files from Teylers objects and load them into the Docker container DB.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
OBJECTS_DIR="$BACKEND_DIR/sample_data/teylers/objects"
PLACES_DIR="$BACKEND_DIR/sample_data/teylers/places"
CONTAINER="nlux-api-1"

python3 "$SCRIPT_DIR/generate_places.py" "$OBJECTS_DIR" "$PLACES_DIR"
docker cp "$PLACES_DIR" "$CONTAINER:/tmp/places"
docker exec "$CONTAINER" python3 scripts/load_data.py /tmp/places/
