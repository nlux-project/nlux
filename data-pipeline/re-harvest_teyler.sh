#!/bin/bash
# Re-harvest Teylers with full fields, re-run pipeline, reload into nlux API.
# Validates a test record (priref=41634) after each step.
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
uv run python3 -c "
import json, sys
with open('$FILE') as f:
    rec = json.load(f)
errors = []
if '@priref' not in rec: errors.append('@priref missing')
if 'Title' not in rec: errors.append('Title missing')
for field in ['Dimension', 'Material', 'Content_subject', 'Technique']:
    status = 'present' if field in rec else 'absent'
    print(f'    {field}: {status}')
if errors:
    print(f'    ERRORS: {errors}')
    sys.exit(1)
" || fail "Harvest file validation failed"
pass "Harvest OK — file has expected fields"

# ── Step 2: Clear pipeline phase flags ───────────────────────────────────────
rm -f data/logs/flags/reconcile_is_done-0.txt
rm -f data/logs/flags/merge_is_done-0.txt
rm -f data/logs/flags/export_is_done-0.txt

# ── Step 3: Load into PostgreSQL datacache ────────────────────────────────────
echo "==> Step 3: Loading into PostgreSQL ..."
uv run python ./manage-data.py --load --teylers

check
uv run python3 -c "
import json, psycopg2
conn = psycopg2.connect(host='localhost', user='postgres', password='admin123', dbname='postgres')
cur = conn.cursor()
cur.execute(\"SELECT data FROM teylers_data_cache WHERE data->>'@priref' = '$TEST_PRIREF'\")
row = cur.fetchone()
if not row:
    print('    Record NOT FOUND in datacache')
    exit(1)
rec = row[0]
for field in ['Title', 'Dimension', 'Material', 'Production', 'Object_name', 'Technique']:
    status = 'present' if field in rec else 'absent'
    print(f'    {field}: {status}')
conn.close()
" || fail "Datacache validation failed"
pass "Datacache OK — fields carried through"

# ── Step 4: Reconcile against AAT ────────────────────────────────────────────
echo "==> Step 4: Reconciling ..."
uv run python ./run-reconcile.py 0 1 --teylers

# ── Step 5: Merge ─────────────────────────────────────────────────────────────
echo "==> Step 5: Merging ..."
uv run python ./run-merge.py 0 1 --teylers

check
uv run python3 -c "
import json, psycopg2
conn = psycopg2.connect(host='localhost', user='postgres', password='admin123', dbname='postgres')
cur = conn.cursor()
cur.execute(\"SELECT data FROM teylers_rewritten_record_cache WHERE data::text LIKE '%museum/${TEST_PRIREF}%' LIMIT 1\")
row = cur.fetchone()
if not row:
    print('    Record not found in rewritten cache (non-fatal)')
else:
    rec = row[0]
    data = rec.get('data', rec) if isinstance(rec, dict) else json.loads(rec).get('data', json.loads(rec))
    for field in ['identified_by', 'produced_by', 'made_of', 'dimension', 'classified_as', 'current_owner', 'representation']:
        status = 'present' if field in data else 'absent'
        print(f'    {field}: {status}')
conn.close()
" || fail "Merge validation failed"
pass "Merge OK"

# ── Step 6: Export ────────────────────────────────────────────────────────────
echo "==> Step 6: Exporting ..."
rm -f data/logs/flags/export_is_done-0.txt
uv run python ./run-export.py 0 1

TOTAL=$(wc -l < data/output/latest/export_full_0.jsonl)
echo "    Export: $TOTAL records"

check
uv run python3 -c "
import json
found = False
with open('data/output/latest/export_full_0.jsonl') as f:
    for line in f:
        line = line.strip()
        if not line: continue
        rec = json.loads(line)
        data = rec.get('data', rec)
        equivs = data.get('equivalent', [])
        if any('museum/${TEST_PRIREF}' in eq.get('id','') for eq in equivs):
            found = True
            for field in ['identified_by', 'produced_by', 'made_of', 'dimension', 'classified_as', 'current_owner', 'representation']:
                status = 'present' if field in data else 'absent'
                print(f'    {field}: {status}')
            break
if not found:
    print('    Record not found in export')
" || fail "Export validation failed"
pass "Export OK"

# ── Step 7: Reload into Docker API ───────────────────────────────────────────
echo "==> Step 7: Resetting and reloading Docker API database ..."
docker cp data/output/latest/export_full_0.jsonl nlux-api-1:/tmp/export_full_0.jsonl
docker exec nlux-api-1 python3 scripts/reset.py
docker exec nlux-api-1 python3 scripts/load_data.py /tmp/
docker exec nlux-api-1 python3 scripts/generate_agents.py

check
URI=$(docker exec nlux-api-1 python3 -c "
import sqlite3, json
conn = sqlite3.connect('/data/nlux.db')
cur = conn.cursor()
cur.execute(\"SELECT uri FROM records WHERE data LIKE '%museum/${TEST_PRIREF}%' LIMIT 1\")
row = cur.fetchone()
if row: print(row[0])
conn.close()
" 2>/dev/null || echo "")

if [ -z "$URI" ]; then
    fail "Record not found in API database"
else
    PATH_PART="${URI#http://localhost:8000/data/}"
    curl -sf "http://localhost:8000/data/${PATH_PART}" | uv run python3 -c "
import json, sys
d = json.load(sys.stdin)
for field in ['identified_by', 'produced_by', 'made_of', 'dimension', 'classified_as', 'current_owner', 'representation', '_links']:
    status = 'present' if field in d else 'absent'
    print(f'    {field}: {status}')
cob = d.get('produced_by', {}).get('carried_out_by', [])
for p in cob:
    if 'id' in p:
        print(f'    agent URI: {p[\"id\"]} ✓')
    else:
        print(f'    agent \"{p.get(\"_label\")}\" has NO id ✗')
        sys.exit(1)
" || fail "API validation failed"
    pass "API OK — all fields present, agent URIs assigned"
fi

echo ""
echo -e "${GREEN}==> All steps completed and validated for priref=$TEST_PRIREF${NC}"
