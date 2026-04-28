#!/bin/bash
set -euo pipefail

cd /Users/lux/data-pipeline

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

pass() { echo -e "  ${GREEN}✓ $1${NC}"; }
fail() { echo -e "  ${RED}✗ $1${NC}"; exit 1; }
check() { echo -e "${YELLOW}  ▸ $1${NC}"; }
run_test() {
    PYTHONDONTWRITEBYTECODE=1 uv run python -m unittest "$1"
}
api_total_items() {
    local scope="$1"
    local term="$2"
    local encoded_q
    encoded_q="$(uv run python - "$term" <<'PY'
import json
import sys
import urllib.parse

term = sys.argv[1]
print(urllib.parse.quote(json.dumps({"text": term, "_lang": "en"})))
PY
)"

    local response
    response="$(curl -sf "http://localhost:8000/api/search/${scope}?q=${encoded_q}&page=1&pageLength=1")"
    API_RESPONSE="$response" uv run python - <<'PY'
import json
import os
import sys

data = json.loads(os.environ["API_RESPONSE"])
print(data["partOf"][0]["totalItems"])
PY
}

echo "==> Testing generated entity export helpers ..."
check "Running tests.test_entity_export"
run_test tests.test_entity_export || fail "Generated entity export tests failed"
pass "Entity export OK — Places, Sets, Concepts, Events, and Agents are collected"

echo "==> Testing backwards-compatible agent export helpers ..."
check "Running tests.test_agent_export"
run_test tests.test_agent_export || fail "Agent export compatibility tests failed"
pass "Agent export OK — existing Person/Group behavior still works"

echo "==> Testing API search for generated Places ..."
check "Searching Places for Amsterdam via localhost:8000"
AMSTERDAM_PLACE_COUNT="$(api_total_items place Amsterdam)" || fail "API place search request failed"
if [ "$AMSTERDAM_PLACE_COUNT" -lt 1 ]; then
    fail "Expected at least 1 Place result for Amsterdam, got $AMSTERDAM_PLACE_COUNT"
fi
pass "API search OK — Amsterdam returns $AMSTERDAM_PLACE_COUNT Place result(s)"

echo ""
echo -e "${GREEN}==> Entity export tests completed successfully${NC}"
