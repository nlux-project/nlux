#!/bin/bash
# Validates a Rijksmuseum Amsterdam test record after each pipeline step.
set -euo pipefail

cd /Users/lux/data-pipeline

TEST_RMA_ID="${1:-200107928}"
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

pass() { echo -e "  ${GREEN}✓ $1${NC}"; }
fail() { echo -e "  ${RED}✗ $1${NC}"; exit 1; }
check() { echo -e "${YELLOW}  ▸ Validating rma id=$TEST_RMA_ID ...${NC}"; }
run_rma_test() {
    TEST_RMA_ID="$TEST_RMA_ID" RMA_REQUIRE_LIVE=1 \
        uv run python -m unittest "tests.test_rma_pipeline.RmaPipelineIntegrationTest.$1"
}

echo "==> Testing RMA ..."
echo "==> Testing Step 1: harvest file validation ..."
check
FILE="data/input/rma/${TEST_RMA_ID}.json"
[ -f "$FILE" ] || fail "Harvest file not found: $FILE"
run_rma_test test_harvest_file || fail "Harvest file validation failed"
pass "Harvest OK - file has expected Linked Art fields"

echo "==> Testing Step 3: datacache validation ..."
check
run_rma_test test_datacache_record || fail "Datacache validation failed"
pass "Datacache OK - fields carried through"

echo "==> Testing Step 4: reconciliation validation ..."
check
run_rma_test test_reconciled_record || fail "Reconciliation validation failed"
pass "Reconciliation OK"

echo "==> Testing Step 5: merge validation ..."
check
run_rma_test test_rewritten_record || fail "Merge validation failed"
pass "Merge OK"

echo "==> Testing Step 6: export validation ..."
check
run_rma_test test_export_record || fail "Export validation failed"
pass "Export OK"

echo "==> Testing Step 7: API validation ..."
check
run_rma_test test_api_record || fail "API validation failed"
pass "API OK - all fields present"

echo ""
echo -e "${GREEN}==> All steps completed and validated for rma id=$TEST_RMA_ID${NC}"
