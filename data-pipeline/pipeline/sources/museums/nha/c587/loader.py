import os
import time
import ujson as json

from pipeline.process.base.loader import Loader


class NhaC587Loader(Loader):
    """Load NHA C587 records from harvested Memorix JSON files."""

    def __init__(self, config):
        Loader.__init__(self, config)
        cfgs = config["all_configs"]
        self.input_dir = os.path.join(cfgs.dumps_dir, "nha-c587")

    def load(self):
        start = time.time()

        if not os.path.isdir(self.input_dir):
            raise FileNotFoundError(
                f"Harvest directory not found: {self.input_dir}\n"
                "Run ./harvest-nha-c587.sh first."
            )

        files = sorted(fn for fn in os.listdir(self.input_dir) if fn.endswith(".json"))
        total = len(files)
        print(f"NHA C587: loading {total} records from {self.input_dir}")

        loaded = 0
        for fn in files:
            path = os.path.join(self.input_dir, fn)
            with open(path, encoding="utf-8") as fh:
                rec = json.load(fh)

            record_id = str(rec.get("id", ""))
            if not record_id:
                continue

            self.out_cache[record_id] = {"data": rec, "identifier": record_id}
            loaded += 1

            if loaded % 1000 == 0:
                elapsed = time.time() - start
                rate = loaded / elapsed if elapsed else 0
                print(f"{loaded}/{total} loaded ({rate:.0f}/s)")

        self.out_cache.commit()
        print(f"NHA C587: loaded {loaded} records in {time.time() - start:.1f}s")
