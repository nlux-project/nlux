import sys
import os
import time
import ujson as json
import requests

WEBAPI = "https://teylers.adlibhosting.com/ais6/webapi/wwwopac.ashx"
PAGE_SIZE = 100

output_dir = sys.argv[1]
session = requests.Session()

def fetch_page(startfrom):
    # Omit the fields parameter to retrieve all available fields per record.
    # The Adlib grouped output uses capitalized group names (Dimension, Material, etc.)
    # that don't match the lowercase field-level names the fields= filter expects.
    url = (
        f"{WEBAPI}?database=museum&search=all&output=json"
        f"&limit={PAGE_SIZE}&startfrom={startfrom}"
    )
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()

start = time.time()
startfrom = 1
x = 0
skipped = 0

first = fetch_page(startfrom)
total = first["adlibJSON"]["diagnostic"]["hits"]
print(f"Harvesting {total} records to {output_dir}/")

while startfrom <= total:
    data = first if startfrom == 1 else fetch_page(startfrom)
    records = data["adlibJSON"]["recordList"].get("record", [])
    if not records:
        break

    for rec in records:
        priref = str(rec.get("@priref", ""))
        if not priref:
            continue
        out_path = os.path.join(output_dir, f"{priref}.json")
        if os.path.exists(out_path):
            skipped += 1
            continue
        with open(out_path, "w") as fh:
            json.dump(rec, fh)
        x += 1

    startfrom += PAGE_SIZE
    elapsed = time.time() - start
    rate = (x + skipped) / elapsed if elapsed else 0
    print(f"  {x + skipped}/{total}  ({rate:.0f}/s, {skipped} skipped)", end="\r", flush=True)

print(f"\nDone: {x} written, {skipped} already existed ({time.time() - start:.1f}s)")
