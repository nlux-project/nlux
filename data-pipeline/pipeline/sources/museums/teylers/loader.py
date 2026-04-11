import os
import time
import ujson as json
from pipeline.process.base.loader import Loader


class TeylersLoader(Loader):
    """Load Teylers Museum objects from pre-harvested JSON files on disk.

    Reads from data/input/teylers/{priref}.json — these files should be
    created by harvest-teylers.sh and enriched by enrich-teylers.py before
    running the loader.
    """

    def __init__(self, config):
        Loader.__init__(self, config)
        self.namespace = config["namespace"]
        cfgs = config["all_configs"]
        self.input_dir = os.path.join(cfgs.dumps_dir, "teylers")

    def load(self):
        start = time.time()

        if not os.path.isdir(self.input_dir):
            raise FileNotFoundError(
                f"Harvest directory not found: {self.input_dir}\n"
                f"Run ./harvest-teylers.sh and enrich-teylers.py first."
            )

        files = sorted(fn for fn in os.listdir(self.input_dir) if fn.endswith(".json"))
        total = len(files)
        print(f"Teylers: loading {total} records from {self.input_dir}")

        x = 0
        for fn in files:
            path = os.path.join(self.input_dir, fn)
            with open(path) as fh:
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
        print(f"Teylers: loaded {x} records in {time.time() - start:.1f}s")
