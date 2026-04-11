TEST_PRIREF="${1:-41634}"
uv run python3 -c "
import json, sys, psycopg2
conn = psycopg2.connect(host='localhost', user='postgres', password='admin123', dbname='postgres')
cur = conn.cursor()
cur.execute(\"SELECT data FROM teylers_data_cache WHERE data->>'@priref' = '${TEST_PRIREF}'\")
row = cur.fetchone()
if not row:
    print('    Record NOT FOUND in datacache')
    sys.exit(1)
rec = row[0]
errors = []
for field in ['Title', 'Dimension', 'Material', 'Production', 'Object_name', 'Technique']:
    if field not in rec:
        errors.append(f'{field}: absent')
conn.close()
if errors:
    print(f'    ERRORS: {errors}')
    sys.exit(1)
else:
    sys.exit(0)
"
