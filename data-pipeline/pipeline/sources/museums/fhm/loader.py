import os
import time
import ujson as json

from pipeline.process.base.loader import Loader


class FhmLoader(Loader):
    """Load Frans Hals Museum records from harvested JSON files."""

    def __init__(self, config):
        Loader.__init__(self, config)
        cfgs = config["all_configs"]
        self.input_dir = os.path.join(cfgs.dumps_dir, "fhm")

    def load(self):
        start = time.time()

        if not os.path.isdir(self.input_dir):
            raise FileNotFoundError(
                f"Harvest directory not found: {self.input_dir}\n"
                "Run ./harvest-fhm.sh first."
            )

        files = sorted(fn for fn in os.listdir(self.input_dir) if fn.endswith(".json"))
        total = len(files)
        print(f"FHM: loading {total} records from {self.input_dir}")

        loaded = 0
        for fn in files:
            path = os.path.join(self.input_dir, fn)
            with open(path, encoding="utf-8") as fh:
                rec = json.load(fh)

            objectid = str(rec.get("objectid", ""))
            if not objectid:
                continue

            self.out_cache[objectid] = {"data": rec, "identifier": objectid}
            loaded += 1

            if loaded % 1000 == 0:
                elapsed = time.time() - start
                rate = loaded / elapsed if elapsed else 0
                print(f"{loaded}/{total} loaded ({rate:.0f}/s)")

        self.out_cache.commit()
        print(f"FHM: loaded {loaded} records in {time.time() - start:.1f}s")
