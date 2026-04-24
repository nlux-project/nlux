import os
import time
import ujson as json

from pipeline.process.base.loader import Loader


class HvhLoader(Loader):
    """Load Huis van Hilde objects from pre-harvested JSON files on disk."""

    def __init__(self, config):
        Loader.__init__(self, config)
        cfgs = config["all_configs"]
        self.input_dir = os.path.join(cfgs.dumps_dir, "hvh")

    def load(self):
        start = time.time()

        if not os.path.isdir(self.input_dir):
            raise FileNotFoundError(
                f"Harvest directory not found: {self.input_dir}\n"
                "Run ./harvest-hvh.sh first."
            )

        files = sorted(fn for fn in os.listdir(self.input_dir) if fn.endswith(".json"))
        total = len(files)
        print(f"HVH: loading {total} records from {self.input_dir}")

        loaded = 0
        for fn in files:
            path = os.path.join(self.input_dir, fn)
            with open(path) as fh:
                rec = json.load(fh)

            identifier = None
            values = rec.get("dc:identifier", [])
            if values:
                identifier = values[0].get("value")
            if not identifier:
                continue

            self.out_cache[identifier] = {"data": rec, "identifier": identifier}
            loaded += 1

            if not loaded % 1000:
                elapsed = time.time() - start
                rate = loaded / elapsed if elapsed else 0
                print(f"{loaded}/{total} loaded ({rate:.0f}/s)")

        self.out_cache.commit()
        print(f"HVH: loaded {loaded} records in {time.time() - start:.1f}s")
