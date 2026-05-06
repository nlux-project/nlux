#!/usr/bin/env bash
# Generate and load all Teylers data into the Docker container DB.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> Loading objects..."
"$SCRIPT_DIR/load_objects_to_docker.sh"

echo "==> Loading Boerhaave objects..."
"$SCRIPT_DIR/load_boerhaave_to_docker.sh"

echo "All done."
