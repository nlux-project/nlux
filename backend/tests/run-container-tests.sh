#!/bin/bash
# Run backend tests that depend on the API container environment.
set -euo pipefail

CONTAINER="${NLUX_API_CONTAINER:-nlux-api-1}"
TEST_DIR="/tmp/nlux-backend-tests"

cd "$(dirname "$0")/.."

docker exec "$CONTAINER" /bin/sh -c "rm -rf '$TEST_DIR' && mkdir -p '$TEST_DIR'"
for test_file in tests/test_*.py; do
    if [ "$(basename "$test_file")" = "test_search_scopes.py" ]; then
        continue
    fi
    docker cp "$test_file" "$CONTAINER:$TEST_DIR/$(basename "$test_file")"
done

docker exec "$CONTAINER" /bin/sh -c \
    "cd /app && PYTHONPATH=/app python3 -m unittest discover -s '$TEST_DIR' -p 'test_*.py'"
