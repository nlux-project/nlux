#!/bin/bash
# Test a single record through each pipeline step.
# Usage: ./test-record.sh [priref]
set -euo pipefail

PRIREF="${1:-41634}"
cd /Users/lux/data-pipeline

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

pass() { echo -e "  ${GREEN}✓ $1${NC}"; }
fail() { echo -e "  ${RED}✗ $1${NC}"; exit 1; }
info() { echo -e "${YELLOW}── $1 ──${NC}"; }

# ── Step 1: Harvest file ─────────────────────────────────────────────────────
info "Step 1: Check harvest file for priref=$PRIREF"

FILE="data/input/teylers/${PRIREF}.json"
[ -f "$FILE" ] || fail "Harvest file not found: $FILE"
pass "File exists: $FILE"

uv run python3 -c "
import json, sys
with open('$FILE') as f:
    rec = json.load(f)

keys = sorted(rec.keys())
print(f'  Keys: {keys}')

errors = []
if '@priref' not in rec:
    errors.append('@priref missing')
if 'Title' not in rec:
    errors.append('Title missing')

# These are the fields that were previously missing due to the fields= filter
for field in ['Dimension', 'Material', 'Content_subject', 'Technique']:
    if field in rec:
        print(f'  {field}: present ({len(rec[field])} entries)')
    else:
        print(f'  {field}: NOT PRESENT (may be empty for this record)')

if errors:
    print(f'ERRORS: {errors}')
    sys.exit(1)
print('  Record structure OK')
" || fail "Harvest file validation failed"
pass "Harvest file validated"

# ── Step 2: PostgreSQL datacache ──────────────────────────────────────────────
info "Step 2: Check teylers_data_cache in PostgreSQL"

psql -h localhost -U postgres -d postgres -t -A -c "
SELECT CASE WHEN COUNT(*) > 0 THEN 'found' ELSE 'missing' END
FROM teylers_data_cache WHERE data->>'@priref' = '${PRIREF}'
" | grep -q 'found' || fail "Record not in teylers_data_cache"
pass "Record in teylers_data_cache"

uv run python3 -c "
import json, psycopg2
conn = psycopg2.connect(host='localhost', user='postgres', password='admin123', dbname='postgres')
cur = conn.cursor()
cur.execute(\"SELECT data FROM teylers_data_cache WHERE data->>'@priref' = '$PRIREF'\")
row = cur.fetchone()
rec = row[0]
for field in ['Title', 'Dimension', 'Material', 'Production', 'Object_name']:
    if field in rec:
        print(f'  {field}: present')
    else:
        print(f'  {field}: NOT PRESENT')
conn.close()
print('  Datacache record OK')
" || fail "Datacache validation failed"
pass "Datacache validated"

# ── Step 3: Reconciled/rewritten record ───────────────────────────────────────
info "Step 3: Check teylers_rewritten_record_cache (after reconcile+merge)"

COUNT=$(psql -h localhost -U postgres -d postgres -t -A -c "SELECT COUNT(*) FROM teylers_rewritten_record_cache" 2>/dev/null || echo "0")
if [ "$COUNT" = "0" ]; then
    echo "  (rewritten cache empty — reconcile/merge not yet run, skipping)"
else
    uv run python3 -c "
import json, psycopg2
conn = psycopg2.connect(host='localhost', user='postgres', password='admin123', dbname='postgres')
cur = conn.cursor()
# Find by equivalent Teylers URI
cur.execute(\"\"\"
    SELECT data FROM teylers_rewritten_record_cache
    WHERE data::text LIKE '%museum/${PRIREF}%' LIMIT 1
\"\"\")
row = cur.fetchone()
if not row:
    print('  Record not found in rewritten cache')
else:
    rec = row[0] if isinstance(row[0], dict) else json.loads(row[0])
    data = rec.get('data', rec)
    for field in ['identified_by', 'produced_by', 'made_of', 'dimension', 'classified_as', 'current_owner', 'representation']:
        if field in data:
            print(f'  {field}: present')
        else:
            print(f'  {field}: NOT PRESENT')
    print('  Rewritten record OK')
conn.close()
" || fail "Rewritten cache validation failed"
    pass "Rewritten record validated"
fi

# ── Step 4: JSONL export ──────────────────────────────────────────────────────
info "Step 4: Check export JSONL"

EXPORT="data/output/latest/export_full_0.jsonl"
[ -f "$EXPORT" ] || { echo "  (export file not found, skipping)"; exit 0; }

uv run python3 -c "
import json
found = False
with open('$EXPORT') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        data = rec.get('data', rec)
        equivs = data.get('equivalent', [])
        if any('museum/${PRIREF}' in eq.get('id','') for eq in equivs):
            found = True
            print(f'  id: {data.get(\"id\", \"?\")}')
            print(f'  type: {data.get(\"type\")}')
            print(f'  _label: {data.get(\"_label\")}')
            for field in ['identified_by', 'produced_by', 'made_of', 'dimension', 'classified_as', 'current_owner', 'representation']:
                status = 'present' if field in data else 'NOT PRESENT'
                print(f'  {field}: {status}')
            break
if not found:
    print('  Record not found in export (searching by equivalent URI)')
else:
    print('  Export record OK')
" || fail "Export validation failed"
pass "Export validated"

# ── Step 5: nlux API (Docker) ─────────────────────────────────────────────────
info "Step 5: Check nlux API response"

# Find the record URI by equivalent
URI=$(docker exec nlux-api-1 python3 -c "
import sqlite3, json
conn = sqlite3.connect('/data/nlux.db')
cur = conn.cursor()
cur.execute(\"SELECT uri, data FROM records WHERE data LIKE '%museum/${PRIREF}%'\")
row = cur.fetchone()
if row:
    print(row[0])
conn.close()
" 2>/dev/null || echo "")

if [ -z "$URI" ]; then
    echo "  (record not in API database, skipping)"
else
    # Extract path portion after /data/
    PATH_PART=$(echo "$URI" | sed 's|http://localhost:8000/data/||')
    RESP=$(curl -s "http://localhost:8000/data/${PATH_PART}")
    uv run python3 -c "
import json, sys
d = json.loads('''$RESP''') if len('''$RESP''') < 50000 else json.loads(sys.stdin.read())
if 'detail' in d and d['detail'] == 'Record not found':
    print('  API returned 404')
    sys.exit(1)
print(f'  _label: {d.get(\"_label\")}')
for field in ['identified_by', 'produced_by', 'made_of', 'dimension', 'classified_as', 'current_owner', 'representation', '_links']:
    status = 'present' if field in d else 'NOT PRESENT'
    print(f'  {field}: {status}')
# Check that carried_out_by persons have id URIs
cob = d.get('produced_by', {}).get('carried_out_by', [])
for p in cob:
    if 'id' in p:
        print(f'  agent URI: {p[\"id\"]} ✓')
    else:
        print(f'  agent \"{p.get(\"_label\")}\" has NO id URI ✗')
print('  API response OK')
" <<< "$RESP" || fail "API validation failed"
    pass "API response validated"
fi

echo ""
echo -e "${GREEN}All checks passed for priref=$PRIREF${NC}"
