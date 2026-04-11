TEST_PRIREF="${1:-41634}"
uv run python3 -c "
import json, sys, psycopg2
conn = psycopg2.connect(host='localhost', user='postgres', password='admin123', dbname='postgres')
cur = conn.cursor()
cur.execute(\"SELECT data FROM teylers_rewritten_record_cache WHERE data::text LIKE '%museum/${TEST_PRIREF}%' LIMIT 1\")
row = cur.fetchone()
if not row:
    print('    Record NOT FOUND in rewritten cache')
    sys.exit(1)
rec = row[0]
data = rec.get('data', rec) if isinstance(rec, dict) else json.loads(rec).get('data', json.loads(rec))
errors = []
for field in ['identified_by', 'produced_by', 'made_of', 'dimension', 'classified_as', 'current_owner', 'representation']:
    if field not in data:
        errors.append(f'{field}: absent')
conn.close()
if errors:
    print(f'    ERRORS: {errors}')
    sys.exit(1)
else:
    sys.exit(0)
"
