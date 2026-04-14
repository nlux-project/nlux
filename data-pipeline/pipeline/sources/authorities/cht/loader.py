import os
import time
import ujson as json
from pipeline.process.base.loader import Loader


class ChtLoader(Loader):
    """Load CHT concepts from pre-harvested JSON files on disk.

    Files are created by harvest-cht.py and stored in data/input/cht/<uuid>.json.
    Each file is a minimal SKOS-in-JSON record produced by the SPARQL harvester.
    """

    def __init__(self, config):
        Loader.__init__(self, config)
        self.namespace = config["namespace"]
        cfgs = config["all_configs"]
        self.input_dir = os.path.join(cfgs.dumps_dir, "cht")

    def load(self):
        start = time.time()

        if not os.path.isdir(self.input_dir):
            raise FileNotFoundError(
                f"CHT harvest directory not found: {self.input_dir}\n"
                "Run harvest-cht.py first."
            )

        files = sorted(fn for fn in os.listdir(self.input_dir) if fn.endswith(".json"))
        total = len(files)
        print(f"CHT: loading {total} records from {self.input_dir}")

        x = 0
        for fn in files:
            path = os.path.join(self.input_dir, fn)
            with open(path) as fh:
                rec = json.load(fh)

            uri = rec.get("id", "")
            if not uri:
                continue

            # Use the UUID portion as the record identifier
            ident = uri.rsplit("/", 1)[-1]
            self.out_cache[ident] = {"data": rec, "identifier": ident}
            x += 1

            if x % 5000 == 0:
                elapsed = time.time() - start
                rate = x / elapsed if elapsed else 0
                print(f"  {x}/{total} loaded ({rate:.0f}/s)")

        self.out_cache.commit()
        print(f"CHT: loaded {x} records in {time.time() - start:.1f}s")
