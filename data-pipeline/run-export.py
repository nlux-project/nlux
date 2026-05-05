import os
import sys
import json
from dotenv import load_dotenv
from pipeline.config import Config
from pipeline.storage.cache.postgres import PoolManager
from pipeline.process.export_splitting import (
    collection_sources_for_record,
    export_filename,
    filter_collection_sources,
    pop_source_filters,
)
from pipeline.process.entity_export import assign_entity_uris, build_entity_record
from pipeline.process.biography_enrichment import enrich_person_record

import datetime
import io
import cProfile
import pstats
from pstats import SortKey
# suppress NotOpenSSLWarning: urllib3
import warnings
warnings.filterwarnings("ignore", module="urllib3")

if "--biographies" in sys.argv:
    sys.exit("The --biographies flag has been removed. Use --export-entities instead.")

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

if "--biography-force" in sys.argv:
    sys.argv.remove("--biography-force")
    biography_force = True
else:
    biography_force = False

export_entity_flags = {"--export-agents", "--export-entities"}
if export_entity_flags.intersection(sys.argv):
    for flag in export_entity_flags:
        if flag in sys.argv:
            sys.argv.remove(flag)
    export_entities = True
else:
    export_entities = False

enrich_biographies = export_entities

biography_languages = ["nl", "en"]
for arg in list(sys.argv):
    if arg.startswith("--biography-languages="):
        sys.argv.remove(arg)
        biography_languages = [
            lang.strip()
            for lang in arg.split("=", 1)[1].split(",")
            if lang.strip()
        ]

selected_sources = pop_source_filters(sys.argv, cfgs.internal.keys())

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

writers = {}


def get_writer(source_name):
    if source_name not in writers:
        fn = os.path.join(cfgs.exports_dir, export_filename(source_name, my_slice))
        writers[source_name] = open(fn, "w", buffering=1)
    return writers[source_name]


try:
    x = 0
    seen = 0
    enriched_biographies = 0
    entities_by_source = {}
    if selected_sources:
        print(f"Exporting selected collections: {', '.join(sorted(selected_sources))}")
    for rec in merged.iter_records_slice(my_slice, max_slice):
        seen += 1
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
        source_names = collection_sources_for_record(rec, data, cfgs)
        source_names = filter_collection_sources(source_names, selected_sources)
        if not source_names:
            if seen % 1000 == 0:
                sys.stdout.write(f"\nScanned {seen} merged records, exported {x} matching records")
                sys.stdout.flush()
            continue
        if export_entities:
            data = dict(data)
            entities = {}
            assign_entity_uris(data, entities, base_uri)
            for source_name in source_names:
                source_entities = entities_by_source.setdefault(source_name, {})
                source_entities.update(entities)
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
        for source_name in source_names:
            outh = get_writer(source_name)
            outh.write(jstr)
            outh.write("\n")
        sys.stdout.write(".")
        sys.stdout.flush()
        x += 1
        if x % 1000 == 0:
            sys.stdout.write(f"\nExported {x} records")
            sys.stdout.flush()
        if profiling and x >= 10000:
            break
    if export_entities:
        for source_name, entities in sorted(entities_by_source.items()):
            outh = get_writer(source_name)
            print(f"\nExporting {len(entities)} generated entity records for {source_name}")
            for entity_count, (uri, info) in enumerate(sorted(entities.items()), start=1):
                data = build_entity_record(uri, info["type"], info["label"], info.get("equivalent"))
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
                if entity_count % 100 == 0:
                    sys.stdout.write(f"\nExported {entity_count} generated entities for {source_name}")
                    sys.stdout.flush()
finally:
    for writer in writers.values():
        writer.close()

if enrich_biographies:
    print(f"\nEnriched {enriched_biographies} Person records with biographies")
if export_entities:
    exported_entities = sum(len(entities) for entities in entities_by_source.values())
    print(f"Exported {exported_entities} generated entity records across collection files")


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
