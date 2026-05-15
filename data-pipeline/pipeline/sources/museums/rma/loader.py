import os
import time
import ujson as json

from pipeline.process.base.loader import Loader


class RmaLoader(Loader):
    """Load Rijksmuseum Amsterdam Linked Art JSON files."""

    def __init__(self, config):
        Loader.__init__(self, config)
        cfgs = config["all_configs"]
        self.input_dir = os.path.join(cfgs.dumps_dir, "rma")

    def _load_file(self, path):
        with open(path, encoding="utf-8") as fh:
            rec = json.load(fh)

        record_id = str(rec.get("id", "")).rstrip("/").rsplit("/", 1)[-1]
        if not record_id:
            return None

        self.out_cache[record_id] = {"data": rec, "identifier": record_id}
        return record_id

    def load_records(self, recids, verbose=False):
        if not os.path.isdir(self.input_dir):
            raise FileNotFoundError(
                f"Harvest directory not found: {self.input_dir}\n"
                "Run ./harvest-rma.sh first."
            )

        loaded = 0
        for recid in recids:
            path = os.path.join(self.input_dir, f"{recid}.json")
            if not os.path.exists(path):
                raise FileNotFoundError(f"Harvest file not found: {path}")
            if verbose:
                print(f"RMA: loading selected file {path}", flush=True)
            if self._load_file(path):
                loaded += 1

        self.out_cache.commit()
        print(f"RMA: loaded {loaded} selected records from {self.input_dir}")

    def load(self, verbose=False):
        start = time.time()

        if not os.path.isdir(self.input_dir):
            raise FileNotFoundError(
                f"Harvest directory not found: {self.input_dir}\n"
                "Run ./harvest-rma.sh first."
            )

        files = sorted(fn for fn in os.listdir(self.input_dir) if fn.endswith(".json"))
        total = len(files)
        print(f"RMA: loading {total} records from {self.input_dir}")

        loaded = 0
        for fn in files:
            path = os.path.join(self.input_dir, fn)
            if verbose and loaded % 100 == 0:
                elapsed = time.time() - start
                print(f"RMA: reading {fn} ({loaded}/{total}, {elapsed:.1f}s)", flush=True)
            if self._load_file(path):
                loaded += 1

            if loaded and loaded % 1000 == 0:
                elapsed = time.time() - start
                rate = loaded / elapsed if elapsed else 0
                print(f"{loaded}/{total} loaded ({rate:.0f}/s)", flush=True)

        self.out_cache.commit()
        print(f"RMA: loaded {loaded} records in {time.time() - start:.1f}s")
