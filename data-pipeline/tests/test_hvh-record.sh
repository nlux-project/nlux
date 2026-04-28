#!/bin/bash
# Validates a test record after each step — exits on first failure.
set -euo pipefail

cd /Users/lux/data-pipeline

TEST_PRIREF="${1:-4564-09}"
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

pass() { echo -e "  ${GREEN}✓ $1${NC}"; }
fail() { echo -e "  ${RED}✗ $1${NC}"; exit 1; }
check() { echo -e "${YELLOW}  ▸ Validating priref=$TEST_PRIREF ...${NC}"; }
run_hvh_test() {
    TEST_PRIREF="$TEST_PRIREF" HVH_REQUIRE_LIVE=1 \
        uv run python -m unittest "tests.test_hvh_pipeline.HvhPipelineIntegrationTest.$1"
}

echo "==> Testing Step 1: harvest file validation ..."
check
FILE="data/input/hvh/${TEST_PRIREF}.json"
[ -f "$FILE" ] || fail "Harvest file not found: $FILE"
run_hvh_test test_harvest_file || fail "Harvest file validation failed"
pass "Harvest + enrich OK — file has expected fields"

echo "==> Testing Step 3: datacache validation ..."
check
run_hvh_test test_datacache_record || fail "Datacache validation failed"
pass "Datacache OK — fields carried through"

echo "==> Testing Step 4: reconciliation validation ..."
check
run_hvh_test test_reconciled_record || fail "Reconciliation validation failed"
pass "Reconciliation OK"

# ── Step 5: Merge ─────────────────────────────────────────────────────────────
echo "==> Testing Step 5: merge validation ..."
check
run_hvh_test test_rewritten_record || fail "Merge validation failed"
pass "Merge OK"

# ── Step 6: Export ────────────────────────────────────────────────────────────
echo "==> Testing Step 6: export validation ..."
check
run_hvh_test test_export_record || fail "Export validation failed"
pass "Export OK"

# ── Step 7: Reload into Docker API ───────────────────────────────────────────
echo "==> Testing Step 7: API validation ..."
check
run_hvh_test test_api_record || fail "API validation failed"
pass "API OK — all fields present, agent URIs assigned"

echo ""
echo -e "${GREEN}==> All steps completed and validated for priref=$TEST_PRIREF${NC}"
