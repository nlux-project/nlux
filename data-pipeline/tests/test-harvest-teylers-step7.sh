TEST_PRIREF="${1:-41634}"
URI=$(docker exec nlux-api-1 python3 -c "
import sqlite3
conn = sqlite3.connect('/data/nlux.db')
cur = conn.cursor()
cur.execute(\"SELECT uri FROM records WHERE data LIKE '%museum/${TEST_PRIREF}%' LIMIT 1\")
row = cur.fetchone()
if row: print(row[0])
conn.close()
" 2>/dev/null || echo "")

if [ -z "$URI" ]; then
    echo "    Record NOT FOUND in API database"
    exit 1
fi

PATH_PART="${URI#http://localhost:8000/data/}"
curl -sf "http://localhost:8000/data/${PATH_PART}" | uv run python3 -c "
import json, sys
d = json.load(sys.stdin)
errors = []
for field in ['identified_by', 'produced_by', 'made_of', 'dimension', 'classified_as', 'current_owner', 'representation', '_links']:
    if field not in d:
        errors.append(f'{field}: absent')
cob = d.get('produced_by', {}).get('carried_out_by', [])
for p in cob:
    if 'id' not in p:
        errors.append(f'agent \"{p.get(\"_label\")}\" has NO id')
if errors:
    print(f'    ERRORS: {errors}')
    sys.exit(1)
else:
    sys.exit(0)
"
