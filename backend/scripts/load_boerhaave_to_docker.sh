#!/usr/bin/env bash
# Generate and load Rijksmuseum Boerhaave data into the Docker container DB.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
BOERHAAVE_HTML="${HOME}/Downloads/Selectie.html"
OBJECTS_DIR="$BACKEND_DIR/sample_data/boerhaave/objects"
CONTAINER="nlux-api-1"

echo "==> Generating Boerhaave object JSON files..."
python3 "$SCRIPT_DIR/generate_boerhaave.py" "$BOERHAAVE_HTML" "$OBJECTS_DIR"

echo "==> Loading Boerhaave objects into Docker container..."
docker cp "$OBJECTS_DIR" "$CONTAINER:/tmp/boerhaave_objects"
docker exec "$CONTAINER" python3 scripts/load_data.py /tmp/boerhaave_objects/

echo "Done."
