import os
import sys
import time

import requests
import ujson as json

from pipeline.sources.museums.hvh.parser import parse_list_identifiers_xml, parse_oai_record_xml

# suppress NotOpenSSLWarning: urllib3
import warnings
warnings.filterwarnings("ignore", module="urllib3")

OAI_ENDPOINT = "http://62.221.199.184:17518/oai"
OUTPUT_DIR = sys.argv[1] if len(sys.argv) > 1 else "data/input/hvh"


def make_list_identifiers_uri(token=None):
    if token:
        return f"{OAI_ENDPOINT}?verb=ListIdentifiers&resumptionToken={token}"
    return f"{OAI_ENDPOINT}?verb=ListIdentifiers&metadataPrefix=oai_pnh"


def make_get_record_uri(identifier):
    return f"{OAI_ENDPOINT}?verb=GetRecord&metadataPrefix=oai_pnh&identifier={identifier}"


def fetch_text(session, url):
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    return resp.text


def harvest(output_dir):
    os.makedirs(output_dir, exist_ok=True)
    session = requests.Session()
    session.headers.update({"Accept-Encoding": "gzip, deflate"})

    written = 0
    skipped = 0
    seen = 0
    token = None
    start = time.time()

    while True:
        xml_text = fetch_text(session, make_list_identifiers_uri(token))
        identifiers, token = parse_list_identifiers_xml(xml_text)
        if not identifiers:
            break

        for identifier in identifiers:
            seen += 1
            out_path = os.path.join(output_dir, f"{identifier}.json")
            if os.path.exists(out_path):
                skipped += 1
                continue

            record_xml = fetch_text(session, make_get_record_uri(identifier))
            record = parse_oai_record_xml(record_xml)
            if record is None:
                continue

            with open(out_path, "w") as fh:
                json.dump(record, fh, indent=2)
            written += 1

            if not seen % 100:
                elapsed = time.time() - start
                rate = seen / elapsed if elapsed else 0
                print(f"  {seen} processed ({rate:.1f}/s, {written} written, {skipped} skipped)", flush=True)

        if not token:
            break

    print(f"Done: {written} written, {skipped} already existed ({time.time() - start:.1f}s)")


if __name__ == "__main__":
    harvest(OUTPUT_DIR)
