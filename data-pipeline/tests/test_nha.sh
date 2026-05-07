#!/bin/bash
# Validates NHA C587 records after each step -- exits on first failure.

set -euo pipefail

cd /Users/lux/data-pipeline

TEST_NHA_C587_ID="${1:-F7DDF7EEFB8E11DF9E4D523BC2E286E2}"
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

pass() { echo -e "  ${GREEN}✓ $1${NC}"; }
fail() { echo -e "  ${RED}✗ $1${NC}"; exit 1; }
check() { echo -e "${YELLOW}  ▸ Validating nha-c587 id=$TEST_NHA_C587_ID ...${NC}"; }
run_nha_test() {
    TEST_NHA_C587_ID="$TEST_NHA_C587_ID" NHA_C587_REQUIRE_LIVE=1 \
        uv run python -m unittest "tests.test_nha_pipeline.NhaC587PipelineIntegrationTest.$1"
}

echo "==> Testing NHA C587 ..."
echo "==> Testing mapper and fetcher configuration ..."
check
run_nha_test test_fetcher_builds_filtered_memorix_requests || fail "Fetcher validation failed"
run_nha_test test_mapper_transforms_record || fail "Mapper validation failed"
pass "Mapper/fetcher OK"

echo "==> Testing Step 1: harvest file validation ..."
check
FILE="data/input/nha/c587/${TEST_NHA_C587_ID}.json"
[ -f "$FILE" ] || fail "Harvest file not found: $FILE"
run_nha_test test_harvest_file || fail "Harvest file validation failed"
pass "Harvest OK -- file has expected fields"

echo "==> Testing Step 3: datacache validation ..."
check
run_nha_test test_datacache_record || fail "Datacache validation failed"
pass "Datacache OK -- fields carried through"

echo "==> Testing Step 4: reconciliation validation ..."
check
run_nha_test test_reconciled_record || fail "Reconciliation validation failed"
pass "Reconciliation OK"

echo "==> Testing Step 6: export validation ..."
check
run_nha_test test_export_record || fail "Export validation failed"
pass "Export OK"

echo ""
echo -e "${GREEN}==> All steps completed and validated for nha-c587 id=$TEST_NHA_C587_ID${NC}"
