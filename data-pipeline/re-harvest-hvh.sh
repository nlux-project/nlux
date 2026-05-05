#!/bin/bash
# Re-harvest Huis van Hilde, re-run pipeline, reload into nlux API.
# Validates a test record after each step -- exits on first failure.
set -euo pipefail

cd /Users/lux/data-pipeline

TEST_HVH_ID="${1:-5061-06}"
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

pass() { echo -e "  ${GREEN}✓ $1${NC}"; }
fail() { echo -e "  ${RED}✗ $1${NC}"; exit 1; }
check() { echo -e "${YELLOW}  ▸ Validating hvh id=$TEST_HVH_ID ...${NC}"; }
run_hvh_test() {
    TEST_HVH_ID="$TEST_HVH_ID" HVH_REQUIRE_LIVE=1 \
        uv run python -m unittest "tests.test_hvh_pipeline.HvhPipelineIntegrationTest.$1"
}

# -- Step 1: Re-harvest -------------------------------------------------------
echo "==> Harvesting Huis van Hilde from OAI-PMH ..."
./harvest-hvh.sh

check
FILE="data/input/hvh/${TEST_HVH_ID}.json"
[ -f "$FILE" ] || fail "Harvest file not found: $FILE"
run_hvh_test test_harvest_file || fail "Harvest file validation failed"
pass "Harvest OK -- file has expected fields"

# -- Step 2: Clear pipeline phase flags --------------------------------------
rm -f data/logs/flags/reconcile_is_done-0.txt
rm -f data/logs/flags/merge_is_done-0.txt
rm -f data/logs/flags/export_is_done-0.txt

# -- Step 3: Load into PostgreSQL datacache ----------------------------------
echo "==> Step 3: Loading into PostgreSQL ..."
uv run python ./manage-data.py --load --hvh

check
run_hvh_test test_datacache_record || fail "Datacache validation failed"
pass "Datacache OK -- fields carried through"

# -- Step 4: Reconcile --------------------------------------------------------
echo "==> Step 4: Reconciling (AAT) ..."
psql -h localhost -U postgres -d postgres -c "TRUNCATE hvh_rewritten_record_cache, hvh_record_cache, merged_merged_record_cache;"
uv run python ./run-reconcile.py 0 1 --hvh

check
run_hvh_test test_reconciled_record || fail "Reconciliation validation failed"
pass "Reconciliation OK"

# -- Step 5: Merge ------------------------------------------------------------
echo "==> Step 5: Merging ..."
uv run python ./run-merge.py 0 1 --hvh

check
run_hvh_test test_rewritten_record || fail "Merge validation failed"
pass "Merge OK"

# -- Step 6: Export -----------------------------------------------------------
echo "==> Step 6: Exporting with generated entities and biographies ..."
psql -h localhost -U postgres -d postgres -c "TRUNCATE marklogic_merged_record_cache, marklogic_data_cache;"
rm -f data/logs/flags/export_is_done-0.txt
uv run python ./run-export.py 0 1 --hvh --export-entities

TOTAL=$(wc -l < data/output/latest/export_hvh_0.jsonl)
echo "    Export: $TOTAL records"

check
run_hvh_test test_export_record || fail "Export validation failed"
pass "Export OK"

# -- Step 7: Reload into Docker API ------------------------------------------
echo "==> Step 7: Resetting and reloading Docker API database ..."
docker cp data/output/latest/export_hvh_0.jsonl nlux-api-1:/tmp/export_hvh_0.jsonl
docker exec nlux-api-1 python3 scripts/reset.py
docker exec nlux-api-1 python3 scripts/load_data.py /tmp/export_hvh_0.jsonl
docker exec nlux-api-1 python3 scripts/generate_agents.py
docker exec nlux-api-1 python3 scripts/generate_concepts.py

check
run_hvh_test test_api_record || fail "API validation failed"
pass "API OK -- all fields present, entity records and biographies available"

echo ""
echo -e "${GREEN}==> All steps completed and validated for hvh id=$TEST_HVH_ID${NC}"
