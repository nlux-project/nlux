import time
import requests
import ujson as json
from pipeline.process.base.loader import Loader

WEBAPI = "https://teylers.adlibhosting.com/ais6/webapi/wwwopac.ashx"
PAGE_SIZE = 100


class TeylersLoader(Loader):
    """Load all Teylers Museum objects by paging through the Adlib webapi."""

    def __init__(self, config):
        Loader.__init__(self, config)
        self.namespace = config["namespace"]
        self.session = requests.Session()

    def _fetch_page(self, startfrom):
        # Omit the fields parameter to retrieve all available fields.
        url = (
            f"{WEBAPI}?database=museum"
            f"&search=all"
            f"&output=json"
            f"&limit={PAGE_SIZE}"
            f"&startfrom={startfrom}"
        )
        resp = self.session.get(url, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def load(self):
        start = time.time()
        x = 0
        startfrom = 1

        first = self._fetch_page(startfrom)
        total = first["adlibJSON"]["diagnostic"]["hits"]
        self.total = total
        print(f"Teylers: {total} records to load")

        while startfrom <= total:
            if startfrom == 1:
                data = first
            else:
                data = self._fetch_page(startfrom)

            records = data["adlibJSON"]["recordList"].get("record", [])
            if not records:
                break

            for rec in records:
                priref = str(rec.get("@priref", ""))
                if not priref:
                    continue
                self.out_cache[priref] = {"data": rec, "identifier": priref}
                x += 1

            startfrom += PAGE_SIZE
            if not x % 1000:
                elapsed = time.time() - start
                rate = x / elapsed if elapsed else 0
                print(f"{x}/{total} loaded ({rate:.0f}/s)")

        self.out_cache.commit()
        print(f"Teylers: loaded {x} records in {time.time() - start:.1f}s")
