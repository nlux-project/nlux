import sys
import os
import time
import ujson as json
import requests

WEBAPI = "https://teylers.adlibhosting.com/ais6/webapi/wwwopac.ashx"
FIELDS = (
    "priref,object_number,title,title.type,"
    "creator,creator.role,"
    "dating.date.start,dating.date.start.prec,"
    "dating.date.end,dating.date.end.prec,"
    "object_name,material,technique,"
    "dimension,dimension.type,dimension.value,dimension.unit,"
    "content.subject,content.place,"
    "media.reference"
)
PAGE_SIZE = 100

output_dir = sys.argv[1]
session = requests.Session()

def fetch_page(startfrom):
    url = (
        f"{WEBAPI}?database=museum&search=all&output=json"
        f"&limit={PAGE_SIZE}&startfrom={startfrom}&fields={FIELDS}"
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
