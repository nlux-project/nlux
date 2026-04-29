import os
import time
import ujson as json

from pipeline.process.base.loader import Loader


class RbhcLoader(Loader):
    """Load Rijksmuseum Boerhaave collection records from harvested JSON files."""

    def __init__(self, config):
        Loader.__init__(self, config)
        self.namespace = config["namespace"]
        cfgs = config["all_configs"]
        self.input_dir = os.path.join(cfgs.dumps_dir, "rbhc")

    def load(self):
        start = time.time()

        if not os.path.isdir(self.input_dir):
            raise FileNotFoundError(
                f"Harvest directory not found: {self.input_dir}\n"
                "Run ./harvest-rbhc.sh first."
            )

        files = sorted(fn for fn in os.listdir(self.input_dir) if fn.endswith(".json"))
        total = len(files)
        print(f"RBHC: loading {total} records from {self.input_dir}")

        x = 0
        for fn in files:
            path = os.path.join(self.input_dir, fn)
            with open(path, encoding="utf-8") as fh:
                rec = json.load(fh)

            priref = str(rec.get("@priref", ""))
            if not priref:
                continue

            self.out_cache[priref] = {"data": rec, "identifier": priref}
            x += 1

            if x % 1000 == 0:
                elapsed = time.time() - start
                rate = x / elapsed if elapsed else 0
                print(f"{x}/{total} loaded ({rate:.0f}/s)")

        self.out_cache.commit()
        print(f"RBHC: loaded {x} records in {time.time() - start:.1f}s")
