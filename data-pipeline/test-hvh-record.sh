#!/bin/bash
# Test a single Huis van Hilde record through each pipeline step.
# Usage: ./test-hvh-record.sh [identifier]
set -euo pipefail

IDENTIFIER="${1:-5061-06}"
cd /Users/lux/data-pipeline

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

pass() { echo -e "  ${GREEN}✓ $1${NC}"; }
fail() { echo -e "  ${RED}✗ $1${NC}"; exit 1; }
info() { echo -e "${YELLOW}── $1 ──${NC}"; }
run_hvh_test() {
    TEST_HVH_ID="$IDENTIFIER" HVH_REQUIRE_LIVE=1 \
        uv run python -m unittest "tests.test_hvh_pipeline.HvhPipelineTest.$1"
}

# ── Step 1: Harvest file ─────────────────────────────────────────────────────
info "Step 1: Check harvest file for identifier=$IDENTIFIER"

FILE="data/input/hvh/${IDENTIFIER}.json"
[ -f "$FILE" ] || fail "Harvest file not found: $FILE"
pass "File exists"

# ── Step 3: PostgreSQL datacache ──────────────────────────────────────────────
info "Step 3: Check hvh_data_cache in PostgreSQL"

psql -h localhost -U postgres -d postgres -t -A -c "
SELECT CASE WHEN COUNT(*) > 0 THEN 'found' ELSE 'missing' END
FROM hvh_data_cache WHERE identifier = '${IDENTIFIER}'
" | grep -q 'found' || fail "Record not in hvh_data_cache"
pass "Record found in datacache"
run_hvh_test test_datacache_record || fail "Step 3 validation failed"
pass "Datacache validated"

# ── Step 4: Reconciled/mapped record ──────────────────────────────────────────
info "Step 4: Check hvh_record_cache (after reconcile)"

psql -h localhost -U postgres -d postgres -t -A -c "
SELECT CASE WHEN COUNT(*) > 0 THEN 'found' ELSE 'missing' END
FROM hvh_record_cache WHERE identifier = '${IDENTIFIER}'
" | grep -q 'found' || fail "Record not in hvh_record_cache; run: uv run python ./run-reconcile.py --hvh --recid ${IDENTIFIER} --norefs"
pass "Record found in reconciled record cache"
run_hvh_test test_reconciled_record || fail "Step 4 validation failed"
pass "Reconciled record validated"

# ── Step 5: Merged/rewritten record ───────────────────────────────────────────
info "Step 5: Check hvh_rewritten_record_cache (after merge)"

COUNT=$(psql -h localhost -U postgres -d postgres -t -A -c "SELECT COUNT(*) FROM hvh_rewritten_record_cache" 2>/dev/null || echo "0")
if [ "$COUNT" = "0" ]; then
    fail "Rewritten cache empty; run: uv run python ./run-merge.py --hvh --recid ${IDENTIFIER} --norefs"
else
    run_hvh_test test_rewritten_record || fail "Step 5 validation failed"
    pass "Rewritten record validated"
fi

echo ""
echo -e "${GREEN}All checks passed for HvH identifier=$IDENTIFIER${NC}"
