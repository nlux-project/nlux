#!/bin/bash
# Re-harvest Teylers with full fields, re-run pipeline, reload into nlux API.
# Validates a test record after each step — exits on first failure.
set -euo pipefail

cd /Users/lux/data-pipeline

TEST_PRIREF="${1:-41634}"
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

pass() { echo -e "  ${GREEN}✓ $1${NC}"; }
fail() { echo -e "  ${RED}✗ $1${NC}"; exit 1; }
check() { echo -e "${YELLOW}  ▸ Validating priref=$TEST_PRIREF ...${NC}"; }

# ── Step 1: Re-harvest ───────────────────────────────────────────────────────
echo "==> Step 1: Deleting existing harvest files ..."
rm -rf data/input/teylers/
mkdir -p data/input/teylers/

echo "==> Harvesting Teylers from Adlib API ..."
./harvest-teylers.sh

check
FILE="data/input/teylers/${TEST_PRIREF}.json"
[ -f "$FILE" ] || fail "Harvest file not found: $FILE"
./data/tests/test-harvest-teylers-step1.sh "$TEST_PRIREF" || fail "Harvest file validation failed"
pass "Harvest OK — file has expected fields"

# ── Step 2: Clear pipeline phase flags ───────────────────────────────────────
rm -f data/logs/flags/reconcile_is_done-0.txt
rm -f data/logs/flags/merge_is_done-0.txt
rm -f data/logs/flags/export_is_done-0.txt

# ── Step 3: Load into PostgreSQL datacache ────────────────────────────────────
echo "==> Step 3: Loading into PostgreSQL ..."
uv run python ./manage-data.py --load --teylers

check
./data/tests/test-harvest-teylers-step3.sh "$TEST_PRIREF" || fail "Datacache validation failed"
pass "Datacache OK — fields carried through"

# ── Step 4: Reconcile against AAT ────────────────────────────────────────────
echo "==> Step 4: Reconciling ..."
uv run python ./run-reconcile.py 0 1 --teylers

# ── Step 5: Merge ─────────────────────────────────────────────────────────────
echo "==> Step 5: Merging ..."
uv run python ./run-merge.py 0 1 --teylers

check
./data/tests/test-harvest-teylers-step5.sh "$TEST_PRIREF" || fail "Merge validation failed"
pass "Merge OK"

# ── Step 6: Export ────────────────────────────────────────────────────────────
echo "==> Step 6: Exporting ..."
rm -f data/logs/flags/export_is_done-0.txt
uv run python ./run-export.py 0 1

TOTAL=$(wc -l < data/output/latest/export_full_0.jsonl)
echo "    Export: $TOTAL records"

check
./data/tests/test-harvest-teylers-step6.sh "$TEST_PRIREF" || fail "Export validation failed"
pass "Export OK"

# ── Step 7: Reload into Docker API ───────────────────────────────────────────
echo "==> Step 7: Resetting and reloading Docker API database ..."
docker cp data/output/latest/export_full_0.jsonl nlux-api-1:/tmp/export_full_0.jsonl
docker exec nlux-api-1 python3 scripts/reset.py
docker exec nlux-api-1 python3 scripts/load_data.py /tmp/
docker exec nlux-api-1 python3 scripts/generate_agents.py

check
./data/tests/test-harvest-teylers-step7.sh "$TEST_PRIREF" || fail "API validation failed"
pass "API OK — all fields present, agent URIs assigned"

echo ""
echo -e "${GREEN}==> All steps completed and validated for priref=$TEST_PRIREF${NC}"
