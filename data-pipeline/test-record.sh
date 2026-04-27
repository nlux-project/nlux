#!/bin/bash
# Test a single record through each pipeline step (without re-running the pipeline).
# Usage: ./test-record.sh [priref]
set -euo pipefail

PRIREF="${1:-41634}"
cd /Users/lux/data-pipeline

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

pass() { echo -e "  ${GREEN}✓ $1${NC}"; }
fail() { echo -e "  ${RED}✗ $1${NC}"; exit 1; }
info() { echo -e "${YELLOW}── $1 ──${NC}"; }
run_teylers_test() {
    TEST_PRIREF="$PRIREF" TEYLERS_REQUIRE_LIVE=1 \
        uv run python -m unittest "tests.test_teylers_pipeline.TeylersPipelineIntegrationTest.$1"
}

# ── Step 1: Harvest file ─────────────────────────────────────────────────────
info "Step 1: Check harvest file for priref=$PRIREF"

FILE="data/input/teylers/${PRIREF}.json"
[ -f "$FILE" ] || fail "Harvest file not found: $FILE"
pass "File exists"
run_teylers_test test_harvest_file || fail "Step 1 validation failed"
pass "Harvest file validated"

# ── Step 3: PostgreSQL datacache ──────────────────────────────────────────────
info "Step 3: Check teylers_data_cache in PostgreSQL"

psql -h localhost -U postgres -d postgres -t -A -c "
SELECT CASE WHEN COUNT(*) > 0 THEN 'found' ELSE 'missing' END
FROM teylers_data_cache WHERE data->>'@priref' = '${PRIREF}'
" | grep -q 'found' || fail "Record not in teylers_data_cache"
pass "Record found in datacache"
run_teylers_test test_datacache_record || fail "Step 3 validation failed"
pass "Datacache validated"

# ── Step 5: Reconciled/rewritten record ───────────────────────────────────────
info "Step 5: Check teylers_rewritten_record_cache (after reconcile+merge)"

COUNT=$(psql -h localhost -U postgres -d postgres -t -A -c "SELECT COUNT(*) FROM teylers_rewritten_record_cache" 2>/dev/null || echo "0")
if [ "$COUNT" = "0" ]; then
    echo "  (rewritten cache empty — reconcile/merge not yet run, skipping)"
else
    run_teylers_test test_rewritten_record || fail "Step 5 validation failed"
    pass "Rewritten record validated"
fi

# ── Step 6: JSONL export ──────────────────────────────────────────────────────
info "Step 6: Check export JSONL"

EXPORT="data/output/latest/export_full_0.jsonl"
if [ ! -f "$EXPORT" ]; then
    echo "  (export file not found, skipping)"
else
    run_teylers_test test_export_record || fail "Step 6 validation failed"
    pass "Export validated"
fi

# ── Step 7: nlux API (Docker) ─────────────────────────────────────────────────
info "Step 7: Check nlux API response"

if ! docker ps --format '{{.Names}}' | grep -q nlux-api-1; then
    echo "  (nlux-api-1 container not running, skipping)"
else
    run_teylers_test test_api_record || fail "Step 7 validation failed"
    pass "API response validated"
fi

echo ""
echo -e "${GREEN}All checks passed for priref=$PRIREF${NC}"
