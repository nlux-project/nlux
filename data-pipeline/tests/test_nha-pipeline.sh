#!/bin/bash
# Validates an NHA C587 test record after each step -- exits on first failure.
# Validates an NHA C480 test record after each step -- exits on first failure.
# Validates an NHA C1477 test record after each step -- exits on first failure.
set -euo pipefail

cd /Users/lux/data-pipeline

TEST_NHA_C587_ID="${1:-F7DDF7EEFB8E11DF9E4D523BC2E286E2}"
TEST_NHA_C480_ID="${2:-FDA34069BFB4CEAE7E0C6F209BA0105D}"
TEST_NHA_C1477_ID="${3:-FF0BAAB1765121EA4D335EAF59F25216}"
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

pass() { echo -e "  ${GREEN}✓ $1${NC}"; }
fail() { echo -e "  ${RED}✗ $1${NC}"; exit 1; }
check_C480() { echo -e "${YELLOW}  ▸ Validating nha-c480 id=$TEST_NHA_C480_ID ...${NC}"; }
check_C587() { echo -e "${YELLOW}  ▸ Validating nha-c587 id=$TEST_NHA_C587_ID ...${NC}"; }
check_C1477() { echo -e "${YELLOW}  ▸ Validating nha-c1477 id=$TEST_NHA_C1477_ID ...${NC}"; }
run_nha_c480_test() {
    TEST_NHA_C480_ID="$TEST_NHA_C480_ID" NHA_C480_REQUIRE_LIVE=1 \
        uv run python -m unittest "tests.test_nha_pipeline.NhaC480PipelineIntegrationTest.$1"
}
run_nha_c587_test() {
    TEST_NHA_C587_ID="$TEST_NHA_C587_ID" NHA_C587_REQUIRE_LIVE=1 \
        uv run python -m unittest "tests.test_nha_pipeline.NhaC587PipelineIntegrationTest.$1"
}
run_nha_c1477_test() {
    TEST_NHA_C1477_ID="$TEST_NHA_C1477_ID" NHA_C1477_REQUIRE_LIVE=1 \
        uv run python -m unittest "tests.test_nha_pipeline.NhaC1477PipelineIntegrationTest.$1"
}

echo "==> Testing Step 1: harvest file validation ..."
check_C480
FILE="data/input/nha/c480/${TEST_NHA_C480_ID}.json"
[ -f "$FILE" ] || fail "Harvest file not found: $FILE"
run_nha_c480_test test_harvest_file || fail "Harvest file validation failed"
pass "Harvest OK -- file has expected fields"
check_C587
FILE="data/input/nha/c587/${TEST_NHA_C587_ID}.json"
[ -f "$FILE" ] || fail "Harvest file not found: $FILE"
run_nha_c587_test test_harvest_file || fail "Harvest file validation failed"
pass "Harvest OK -- file has expected fields"
check_C1477
FILE="data/input/nha/c1477/${TEST_NHA_C1477_ID}.json"
[ -f "$FILE" ] || fail "Harvest file not found: $FILE"
run_nha_c1477_test test_harvest_file || fail "Harvest file validation failed"
pass "Harvest OK -- file has expected fields"

echo "==> Testing Step 3: datacache validation ..."
check_C480
run_nha_c480_test test_datacache_record || fail "Datacache validation failed"
check_C587
run_nha_c587_test test_datacache_record || fail "Datacache validation failed"
check_C1477
run_nha_c1477_test test_datacache_record || fail "Datacache validation failed"
pass "Datacache OK -- fields carried through"

echo "==> Testing Step 4: reconciliation validation ..."
check_C480
run_nha_c480_test test_reconciled_record || fail "Reconciliation validation failed"
check_C587
run_nha_c587_test test_reconciled_record || fail "Reconciliation validation failed"
check_C1477
run_nha_c1477_test test_reconciled_record || fail "Reconciliation validation failed"
pass "Reconciliation OK"

echo "==> Testing Step 6: export validation ..."
check_C480
run_nha_c480_test test_export_record || fail "Export validation failed"
check_C587
run_nha_c587_test test_export_record || fail "Export validation failed"
check_C1477
run_nha_c1477_test test_export_record || fail "Export validation failed"
pass "Export OK"

echo ""
echo -e "${GREEN}==> All steps completed and validated for nha-c480 id=$TEST_NHA_C480_ID, nha-c587 id=$TEST_NHA_C587_ID, nha-c1477 id=$TEST_NHA_C1477_ID${NC}"
