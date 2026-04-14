#!/usr/bin/env python3
"""
Harvest all terms from the Dutch Cultuurhistorische Thesaurus (CHT) via
the SPARQL endpoint at https://api.linkeddata.cultureelerfgoed.nl/

Each CHT concept is saved as a JSON file in data/input/cht/<uuid>.json.
The files are minimal SKOS-in-JSON records that the ChtLoader (and ChtMapper)
can later process into Linked Art Type/Material stubs.

Usage:
    uv run python harvest-cht.py [--output-dir <dir>]

Options:
    --output-dir    Override the default output directory
                    (default: data/input/cht/ relative to this script)
"""
import json
import os
import sys
import time
import argparse
from pathlib import Path

try:
    import requests
except ImportError:
    print("requests is required: pip install requests")
    sys.exit(1)


# CHT SPARQL endpoint (Triply-powered)
#SPARQL_ENDPOINT = (
    #"https://api.linkeddata.cultureelerfgoed.nl/datasets/rce/cht/sparql"
#)
# CHT SPARQL endpoint (Speedy)
SPARQL_ENDPOINT = (
    "https://api.linkeddata.cultureelerfgoed.nl/datasets/thesauri/Cultuurhistorische-Thesaurus-CHT/sparql"
)
CHT_NAMESPACE = "https://data.cultureelerfgoed.nl/term/id/cht/"

# Fetch all active concepts with Dutch prefLabels, altLabels, broader, and
# skos:exactMatch to AAT where available.
QUERY = """\
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX owl:  <http://www.w3.org/2002/07/owl#>

SELECT DISTINCT ?uri ?prefLabel ?altLabel ?broader ?exactMatch WHERE {
  ?uri a skos:Concept ;
       skos:prefLabel ?prefLabel .
  FILTER(LANG(?prefLabel) = "nl")
  FILTER(STRSTARTS(STR(?uri), "https://data.cultureelerfgoed.nl/term/id/cht/"))
  OPTIONAL {
    ?uri skos:altLabel ?altLabel .
    FILTER(LANG(?altLabel) = "nl")
  }
  OPTIONAL { ?uri skos:broader ?broader }
  OPTIONAL {
    ?uri skos:exactMatch ?exactMatch .
    FILTER(STRSTARTS(STR(?exactMatch), "http://vocab.getty.edu/aat/"))
  }
}
ORDER BY ?uri
"""

PAGE_SIZE = 10_000  # Triply default limit is 10 000


def sparql_fetch(endpoint: str, query: str, offset: int, limit: int) -> list[dict]:
    """Execute a paginated SPARQL SELECT query; return list of binding dicts."""
    paged_query = f"{query}\nLIMIT {limit}\nOFFSET {offset}"
    r = requests.get(
        endpoint,
        params={"query": paged_query},
        headers={"Accept": "application/sparql-results+json"},
        timeout=120,
    )
    r.raise_for_status()
    data = r.json()
    return data["results"]["bindings"]


def build_record(uri: str, rows: list[dict]) -> dict:
    """Build a SKOS-in-JSON record from all SPARQL result rows for one URI."""
    pref_label = ""
    alt_labels: list[str] = []
    broader_uris: set[str] = set()
    exact_matches: set[str] = set()

    for row in rows:
        if not pref_label and "prefLabel" in row:
            pref_label = row["prefLabel"]["value"]
        if "altLabel" in row:
            lbl = row["altLabel"]["value"]
            if lbl not in alt_labels:
                alt_labels.append(lbl)
        if "broader" in row:
            broader_uris.add(row["broader"]["value"])
        if "exactMatch" in row:
            exact_matches.add(row["exactMatch"]["value"])

    rec: dict = {
        "id": uri,
        "type": "Type",          # default; ChtMapper may refine
        "_label": pref_label,
        "prefLabel": pref_label,
    }
    if alt_labels:
        rec["altLabel"] = alt_labels
    if broader_uris:
        rec["broader"] = [{"id": b} for b in sorted(broader_uris)]
    if exact_matches:
        # Store as equivalent list — ChtMapper will carry these forward
        rec["equivalent"] = [{"id": m} for m in sorted(exact_matches)]

    return rec


def harvest(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Harvesting CHT → {output_dir}")
    print(f"Endpoint: {SPARQL_ENDPOINT}")

    # Group rows by URI across pages
    by_uri: dict[str, list[dict]] = {}

    offset = 0
    page = 0
    while True:
        page += 1
        print(f"  Page {page} (offset={offset}) ...", end=" ", flush=True)
        t0 = time.time()
        try:
            rows = sparql_fetch(SPARQL_ENDPOINT, QUERY, offset, PAGE_SIZE)
        except requests.HTTPError as exc:
            print(f"\nHTTP error on page {page}: {exc}")
            sys.exit(1)
        elapsed = time.time() - t0
        print(f"{len(rows)} rows in {elapsed:.1f}s")

        if not rows:
            break

        for row in rows:
            uri = row["uri"]["value"]
            by_uri.setdefault(uri, []).append(row)

        if len(rows) < PAGE_SIZE:
            # Last page
            break
        offset += PAGE_SIZE

    print(f"  {len(by_uri)} unique CHT concepts fetched")

    # Write one JSON file per concept
    written = 0
    for uri, rows in by_uri.items():
        if not uri.startswith(CHT_NAMESPACE):
            continue
        uuid = uri[len(CHT_NAMESPACE):]
        out_file = output_dir / f"{uuid}.json"
        rec = build_record(uri, rows)
        out_file.write_text(json.dumps(rec, ensure_ascii=False, indent=2))
        written += 1

    print(f"  {written} records written to {output_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Harvest CHT thesaurus via SPARQL")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory for JSON files (default: data/input/cht/)",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    output_dir = Path(args.output_dir) if args.output_dir else (script_dir / "data" / "input" / "cht")

    harvest(output_dir)


if __name__ == "__main__":
    main()
