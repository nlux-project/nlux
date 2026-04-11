TEST_PRIREF="${1:-41634}"
PIPELINE=/Users/lux/data-pipeline
EXPORT="${PIPELINE}/data/output/latest/export_full_0.jsonl"
uv run python3 -c "
import json, sys
found = False
with open('${EXPORT}') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        data = rec.get('data', rec)
        equivs = data.get('equivalent', [])
        if any('museum/${TEST_PRIREF}' in eq.get('id', '') for eq in equivs):
            found = True
            errors = []
            for field in ['identified_by', 'produced_by', 'made_of', 'dimension', 'classified_as', 'current_owner', 'representation']:
                if field not in data:
                    errors.append(f'{field}: absent')
            if errors:
                print(f'    ERRORS: {errors}')
                sys.exit(1)
            else:
                sys.exit(0)
if not found:
    print('    Record NOT FOUND in export')
    sys.exit(1)
"
