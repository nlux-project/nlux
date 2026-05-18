#!/bin/bash
# Re-harvest RijksMuseum Amsterdam, re-run pipeline, reload into nlux API.
# Validates a test record after each step -- exits on first failure.
set -euo pipefail

cd /Users/lux/data-pipeline

#uv run python -m unittest tests.test_rma_pipeline
#uv run python ./run-reconcile.py --rma --recid 20010

TEST_OBJECTID="${1:-20050479}"
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

pass() { echo -e "  ${GREEN}✓ $1${NC}"; }
fail() { echo -e "  ${RED}✗ $1${NC}"; exit 1; }
check() { echo -e "${YELLOW}  ▸ Validating objectid=$TEST_OBJECTID ...${NC}"; }
run_rma_test() {
    TEST_OBJECTID="$TEST_OBJECTID" RMA_REQUIRE_LIVE=1 \
        uv run python -m unittest "tests.test_rma_pipeline.RmaPipelineIntegrationTest.$1"
}

# -- test : harvested file ----------------------------------
echo "==> Step: harvested file ..."
check
FILE="/Users/lux/data-pipeline/data/input/rma/${TEST_OBJECTID}.json"
[ -f "$FILE" ] || fail "Harvest file not found: $FILE"
run_rma_test test_harvest_file || fail "Harvest file validation failed"
pass "Harvest OK -- file has expected fields"


# -- Step 3: Load into PostgreSQL datacache ----------------------------------
echo "==> Step 3: Loading into PostgreSQL ..."
#uv run python ./manage-data.py --load --rma --recid ${TEST_OBJECTID}

#check
#run_rma_test test_datacache_record || fail "Datacache validation failed"
#pass "Datacache OK -- fields carried through"

# -- Step 4: Reconcile --------------------------------------------------------
echo "==> Step 4: Reconciling (AAT) ..."
#psql -h localhost -U postgres -d postgres -c "TRUNCATE rma_rewritten_record_cache, rma_record_cache, merged_merged_record_cache;"
uv run python ./run-reconcile.py --rma --recid ${TEST_OBJECTID} --norefs

check
run_rma_test test_reconciled_record || fail "Reconciliation validation failed"
pass "Reconciliation OK"

# -- Step 5: Merge ------------------------------------------------------------
echo "==> Step 5: Merging ..."
uv run python ./run-merge.py --rma --recid ${TEST_OBJECTID}

check
run_rma_test test_rewritten_record || fail "Merge validation failed"
pass "Merge OK"

exit 0

# -- Step 6: Export -----------------------------------------------------------
echo "==> Step 6: Exporting with generated entities and biographies ..."
#psql -h localhost -U postgres -d postgres -c "TRUNCATE marklogic_merged_record_cache, marklogic_data_cache;"
#rm -f data/logs/flags/export_is_done-0.txt
#uv run python ./run-export.py 0 1 --rma --export-entities --recid ${TEST_OBJECTID}
uv run python ./run-export.py 0 1 --rma --export-entities

#TOTAL=$(wc -l < data/output/latest/export_rma_0.jsonl)
#echo "    Export: $TOTAL records"

check
run_rma_test test_export_record || fail "Export validation failed"
pass "Export OK"

# -- Step 7: Reload into Docker API ------------------------------------------
echo "==> Step 7: Resetting and reloading Docker API database ..."
docker cp data/output/latest/export_rma_0.jsonl nlux-api-1:/tmp/export_rma_0.jsonl
#docker exec nlux-api-1 python3 scripts/reset.py
docker exec nlux-api-1 python3 scripts/load_data.py /tmp/export_rma_0.jsonl
docker exec nlux-api-1 python3 scripts/generate_agents.py
docker exec nlux-api-1 python3 scripts/generate_concepts.py

check
run_rma_test test_api_record || fail "API validation failed"
pass "API OK -- all fields present, entity records and biographies available"

echo ""
echo -e "${GREEN}==> All steps completed and validated for objectid=$TEST_OBJECTID${NC}"
