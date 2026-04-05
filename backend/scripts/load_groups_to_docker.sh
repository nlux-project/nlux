#!/usr/bin/env bash
# Generate Group JSON files from Teylers objects and load them into the Docker container DB.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
OBJECTS_DIR="$BACKEND_DIR/sample_data/teylers/objects"
GROUPS_DIR="$BACKEND_DIR/sample_data/teylers/groups"
CONTAINER="nlux-api-1"

python3 "$SCRIPT_DIR/generate_groups.py" "$OBJECTS_DIR" "$GROUPS_DIR"
docker cp "$GROUPS_DIR" "$CONTAINER:/tmp/groups"
docker exec "$CONTAINER" python3 scripts/load_data.py /tmp/groups/
