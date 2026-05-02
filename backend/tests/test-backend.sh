#!/bin/bash
# Run the backend unittest suite from bash.
set -euo pipefail

cd "$(dirname "$0")/.."

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
pass() { echo -e "  ${GREEN}✓ $1${NC}"; }
fail() { echo -e "  ${RED}✗ $1${NC}"; exit 1; }
step() { echo -e "${YELLOW}==> $1${NC}"; }

step "Running local backend tests"
PYTHONPYCACHEPREFIX=/tmp/nlux-pycache python3 -m unittest tests.test_search_scopes \
    || fail "Local backend tests failed"
pass "Local backend tests OK"

step "Running API-container backend tests"
./tests/run-container-tests.sh \
    || fail "API-container backend tests failed"
pass "API-container backend tests OK"

echo ""
echo -e "${GREEN}==> Backend test suite completed${NC}"
