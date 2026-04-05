#!/usr/bin/env bash
# Generate Person JSON files from Teylers objects and load them into the Docker container DB.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
OBJECTS_DIR="$BACKEND_DIR/sample_data/teylers/objects"
PERSONS_DIR="$BACKEND_DIR/sample_data/teylers/persons"
CONTAINER="nlux-api-1"

python3 "$SCRIPT_DIR/generate_persons.py" "$OBJECTS_DIR" "$PERSONS_DIR"
docker cp "$PERSONS_DIR" "$CONTAINER:/tmp/persons"
docker exec "$CONTAINER" python3 scripts/load_data.py /tmp/persons/
