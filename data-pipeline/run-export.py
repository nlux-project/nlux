import os
import sys
import json
from dotenv import load_dotenv
from pipeline.config import Config
from pipeline.storage.cache.postgres import PoolManager
from pipeline.process.agent_export import assign_agent_uris, build_agent_record
from pipeline.process.biography_enrichment import enrich_person_record

import datetime
import io
import cProfile
import pstats
from pstats import SortKey

load_dotenv()
basepath = os.getenv("LUX_BASEPATH", "")
cfgs = Config(basepath=basepath)
idmap = cfgs.get_idmap()
cfgs.cache_globals()
cfgs.instantiate_all()

merged = cfgs.results["merged"]["recordcache"]
ml = cfgs.results["marklogic"]["recordcache"]
mapper = cfgs.results["marklogic"]["mapper"]

if "--profile" in sys.argv:
    sys.argv.remove("--profile")
    profiling = True
else:
    profiling = False

if "--biographies" in sys.argv:
    sys.argv.remove("--biographies")
    enrich_biographies = True
else:
    enrich_biographies = False

if "--biography-force" in sys.argv:
    sys.argv.remove("--biography-force")
    biography_force = True
else:
    biography_force = False

if "--export-agents" in sys.argv:
    sys.argv.remove("--export-agents")
    export_agents = True
else:
    export_agents = enrich_biographies

biography_languages = ["nl", "en"]
for arg in list(sys.argv):
    if arg.startswith("--biography-languages="):
        sys.argv.remove(arg)
        biography_languages = [
            lang.strip()
            for lang in arg.split("=", 1)[1].split(",")
            if lang.strip()
        ]

if len(sys.argv) > 2:
    my_slice = int(sys.argv[1])
    max_slice = int(sys.argv[2])
else:
    my_slice = 0
    max_slice = 1

# Only reading from idmap, not writing, so can cache
idmap.enable_memory_cache()

if profiling:
    pr = cProfile.Profile()
    pr.enable()

if not os.path.exists(cfgs.exports_dir):
    os.mkdir(cfgs.exports_dir)

base_uri = (
    cfgs.internal_uri.rsplit("data/", 1)[0]
    if cfgs.internal_uri.endswith("/data/") or cfgs.internal_uri.endswith("data/")
    else cfgs.internal_uri
)

fn = os.path.join(cfgs.exports_dir, f"export_full_{my_slice}.jsonl")
with open(fn, "w") as outh:
    x = 0
    enriched_biographies = 0
    agents = {}
    for rec in merged.iter_records_slice(my_slice, max_slice):
        yuid = rec["yuid"]
        if not yuid in ml:
            try:
                rec2 = mapper.transform(rec, rec["data"]["type"])
            except Exception as e:
                print(f"{yuid} errored in marklogic mapper: {e}")
                continue
            # Extract data BEFORE storing to ml (the store commits to
            # PostgreSQL which can invalidate the merged iterator's cursor)
            data = dict(rec2["data"]) if isinstance(rec2, dict) and "data" in rec2 else rec2
            ml[yuid] = rec2
        else:
            data = ml[yuid]["data"]
        if export_agents:
            data = dict(data)
            assign_agent_uris(data, agents, base_uri)
        if enrich_biographies and data.get("type") == "Person":
            try:
                data, qid = enrich_person_record(
                    dict(data),
                    biography_languages,
                    base_uri,
                    force=biography_force,
                )
                if qid:
                    enriched_biographies += 1
            except Exception as e:
                print(f"{yuid} errored in biography enrichment: {e}")
        jstr = json.dumps(data, separators=(",", ":"),
                          default=lambda o: o.isoformat() if isinstance(o, datetime.datetime) else str(o))
        outh.write(jstr)
        outh.write("\n")
        sys.stdout.write(".")
        sys.stdout.flush()
        x += 1
        if profiling and x >= 10000:
            break
    if export_agents:
        for uri, info in sorted(agents.items()):
            data = build_agent_record(uri, info["type"], info["label"])
            if enrich_biographies and data.get("type") == "Person":
                try:
                    data, qid = enrich_person_record(
                        data,
                        biography_languages,
                        base_uri,
                        force=biography_force,
                    )
                    if qid:
                        enriched_biographies += 1
                except Exception as e:
                    print(f"{uri} errored in biography enrichment: {e}")
            jstr = json.dumps(
                data,
                separators=(",", ":"),
                default=lambda o: o.isoformat()
                if isinstance(o, datetime.datetime)
                else str(o),
            )
            outh.write(jstr)
            outh.write("\n")

if enrich_biographies:
    print(f"\nEnriched {enriched_biographies} Person records with biographies")
if export_agents:
    print(f"Exported {len(agents)} generated Person/Group records")


if profiling:
    pr.disable()
    s = io.StringIO()
    sortby = SortKey.CUMULATIVE
    # sortby = SortKey.TIME
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    ps.print_stats()
    print(s.getvalue())
    raise ValueError()

# Explicitly force all postgres connections to close
poolman = PoolManager.get_instance()
poolman.put_all("localsocket")

with open(os.path.join(cfgs.log_dir, "flags", f"export_is_done-{my_slice}.txt"), "w") as fh:
    fh.write("1\n")
