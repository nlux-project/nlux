TEST_PRIREF="${1:-41634}"
PIPELINE=/Users/lux/data-pipeline
FILE="${PIPELINE}/data/input/teylers/${TEST_PRIREF}.json"
[ -f "$FILE" ] || fail "Harvest file not found: $FILE"
uv run python3 -c "
import json, sys
with open('$FILE') as f:
    rec = json.load(f)
errors = []
if '@priref' not in rec: errors.append('@priref missing')
if '@created' not in rec: errors.append('@created missing')
if '@modification' not in rec: errors.append('@modification missing')
for field in ['Title', 'Description', 'Dimension', 'Material', 'Production', 'Object_category', 'Object_name', 'Technique']:
    status = 'present' if field in rec else 'absent'
    if status == 'absent':
        errors.append(f'{field}: {status}')
if errors:
    print(f'    ERRORS: {errors}')
    sys.exit(1) 
else:
    sys.exit(0)
"
