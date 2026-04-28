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

echo "==> Testing generated entity export helpers ..."
check "Running tests.test_entity_export"
run_test tests.test_entity_export || fail "Generated entity export tests failed"
pass "Entity export OK — Places, Sets, Concepts, Events, and Agents are collected"

echo "==> Testing backwards-compatible agent export helpers ..."
check "Running tests.test_agent_export"
run_test tests.test_agent_export || fail "Agent export compatibility tests failed"
pass "Agent export OK — existing Person/Group behavior still works"

echo ""
echo -e "${GREEN}==> Entity export tests completed successfully${NC}"
