#!/usr/bin/env python3
"""
Parse the Rijksmuseum Boerhaave HTML export (Selectie.html) and generate
Linked Art HumanMadeObject JSON files.

Usage:
    python scripts/generate_boerhaave.py <html_file> <output_dir>

Example:
    python scripts/generate_boerhaave.py ~/Downloads/Selectie.html sample_data/boerhaave/objects/
"""
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

LINKED_ART_CONTEXT = "https://linked.art/ns/v1/linked-art.json"
BASE_URI = "https://mmb-web.adlibhosting.com/ais6/Details/museum/"
BASE_PERSON_URI = "https://mmb-web.adlibhosting.com/nlux/person/"
BASE_GROUP_URI = "https://mmb-web.adlibhosting.com/nlux/group/"
BASE_PLACE_URI = "https://mmb-web.adlibhosting.com/nlux/place/"
CATALOG_BASE = "https://mmb-web.adlibhosting.com/ais6/Details/museum/"

AAT_PREFERRED_NAME = "http://vocab.getty.edu/aat/300404670"
AAT_ACCESSION_NUMBER = "http://vocab.getty.edu/aat/300312355"
AAT_WEB_PAGE = "http://vocab.getty.edu/aat/300264578"
AAT_DESCRIPTION = "http://vocab.getty.edu/aat/300411780"
AAT_MAKING = "http://vocab.getty.edu/aat/300386171"
AAT_DESIGNING = "http://vocab.getty.edu/aat/300404387"


def slugify(name: str) -> str:
    slug = name.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug


class BoerhaaveParser(HTMLParser):
    """Simple parser that extracts record blocks from the Boerhaave HTML export."""

    def __init__(self):
        super().__init__()
        self.records = []
        self._in_record = False
        self._current = {}
        self._tag_stack = []
        self._current_text = ""
        self._in_strong = False
        self._in_em = False
        self._divs = []
        self._in_td_content = False
        self._img_src = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "div" and attrs.get("class") == "record":
            self._in_record = True
            self._current = {"divs": [], "makers": [], "img": None}
            self._divs = []
        if self._in_record:
            if tag == "strong":
                self._in_strong = True
                self._current_text = ""
            if tag == "em":
                self._in_em = True
                self._current_text = ""
            if tag == "img" and "src" in attrs:
                self._current["img"] = attrs["src"]
            if tag == "div":
                self._current_text = ""

    def handle_endtag(self, tag):
        if not self._in_record:
            return
        if tag == "strong":
            self._in_strong = False
            self._current["title"] = self._current_text.strip()
        if tag == "em":
            self._in_em = False
            text = self._current_text.strip().rstrip("‎").strip()
            if text:
                self._current["makers"].append(text)
        if tag == "div" and self._in_record:
            text = self._current_text.strip()
            if text:
                self._divs.append(text)
            self._current_text = ""
        if tag == "table" and self._in_record:
            # Assign parsed divs: [title_already_set, maker_already_set, date, type, accession]
            non_title = [d for d in self._divs if d != self._current.get("title", "")]
            # divs inside td: date, object_type, accession_number
            candidates = [d for d in non_title if not any(m in d for m in self._current.get("makers", []))]
            if len(candidates) >= 3:
                self._current["date"] = candidates[-3]
                self._current["object_type"] = candidates[-2]
                self._current["accession"] = candidates[-1]
            elif len(candidates) >= 1:
                self._current["accession"] = candidates[-1]
        if tag == "div" and self._in_record and self._divs and "accession" in self._current:
            self._in_record = False
            self.records.append(self._current)

    def handle_data(self, data):
        if self._in_record:
            self._current_text += data


def parse_maker(maker_str: str):
    """
    Parse a maker string like:
      ' Etienne; Parijs Lenoir (Maker)'
      ' J.W.; Delft Giltay (Maker)'
      ' Alexander Graham Bell (Ontwerper)'
      'Cern; Genève (Maker)'
    Returns: (name, place_or_none, role)
    """
    # Strip leading/trailing whitespace and leading commas (multiple <em> elements are comma-separated)
    maker_str = maker_str.strip().lstrip(",").strip()
    role = "Maker"
    if "(Ontwerper)" in maker_str:
        role = "Ontwerper"
    name_part = re.sub(r"\(.*?\)", "", maker_str).strip().rstrip(",").strip()

    # Try to separate "Firstname; Place Lastname" pattern
    if ";" in name_part:
        parts = name_part.split(";", 1)
        first = parts[0].strip()
        rest = parts[1].strip().split()
        if rest:
            place = rest[0]
            last = " ".join(rest[1:]) if len(rest) > 1 else ""
            name = f"{first} {last}".strip() if last else first
            return name, place, role
    return name_part, None, role


def guess_agent_type(name: str) -> str:
    """Guess whether an agent is a Person or Group based on name heuristics."""
    group_hints = ["Cern", "Instrumentmakerij", "Pistor",
                   "Onbekend", "und ", "Museum", "Bosch", "Luzac", "Ottens",
                   "Baudouin", "Dilly", "Roycroft"]
    for hint in group_hints:
        if hint.lower() in name.lower():
            return "Group"
    return "Person"


def parse_date_range(date_str: str):
    """Parse '1796 - 1796' or '1675 - 1725' into begin/end ISO strings."""
    parts = date_str.split(" - ")
    if len(parts) == 2:
        begin = parts[0].strip()
        end = parts[1].strip()
        return f"{begin}-01-01", f"{end}-12-31", date_str.strip()
    return None, None, date_str.strip()


def build_agent(name: str, place: str = None, role: str = "Maker") -> dict:
    agent_type = guess_agent_type(name)
    base = BASE_PERSON_URI if agent_type == "Person" else BASE_GROUP_URI
    agent = {
        "type": agent_type,
        "_label": name,
        "id": base + slugify(name),
    }
    return agent, place


def build_record(rec: dict) -> dict:
    accession = rec.get("accession", "").strip()
    title = rec.get("title", "").strip()
    date_str = rec.get("date", "").strip()
    object_type = rec.get("object_type", "").strip()
    img_src = rec.get("img")
    makers_raw = rec.get("makers", [])

    uri = BASE_URI + accession

    begin, end, date_label = parse_date_range(date_str)

    # Parse makers and designers
    makers = []
    designers = []
    for m in makers_raw:
        agent, place = build_agent(*parse_maker(m)[:2], parse_maker(m)[2])
        if parse_maker(m)[2] == "Ontwerper":
            designers.append((agent, place))
        else:
            makers.append((agent, place))

    # Build produced_by
    produced_parts = []
    for agent, place in makers:
        part = {
            "type": "Production",
            "classified_as": [{"id": AAT_MAKING, "_label": "making"}],
            "carried_out_by": [agent],
        }
        if place:
            part["took_place_at"] = [{
                "type": "Place",
                "_label": place,
                "id": BASE_PLACE_URI + slugify(place),
            }]
        produced_parts.append(part)

    for agent, place in designers:
        part = {
            "type": "Production",
            "classified_as": [{"id": AAT_DESIGNING, "_label": "designing"}],
            "carried_out_by": [agent],
        }
        produced_parts.append(part)

    produced_by: dict = {"type": "Production"}
    if len(produced_parts) == 1:
        produced_by.update({k: v for k, v in produced_parts[0].items() if k != "type"})
    elif len(produced_parts) > 1:
        produced_by["part"] = produced_parts

    if begin:
        produced_by["timespan"] = {
            "type": "TimeSpan",
            "begin_of_the_begin": begin,
            "end_of_the_end": end,
            "identified_by": [{"type": "Name", "content": date_label}],
        }

    record = {
        "@context": LINKED_ART_CONTEXT,
        "id": uri,
        "type": "HumanMadeObject",
        "_label": title,
        "identified_by": [
            {
                "type": "Name",
                "content": title,
                "classified_as": [{"id": AAT_PREFERRED_NAME, "_label": "preferred name"}],
            },
            {
                "type": "Identifier",
                "content": accession,
                "classified_as": [{"id": AAT_ACCESSION_NUMBER, "_label": "accession number"}],
                "assigned_by": [{"type": "AttributeAssignment", "carried_out_by": [
                    {"type": "Group", "_label": "Rijksmuseum Boerhaave",
                     "id": BASE_GROUP_URI + "rijksmuseum-boerhaave"}
                ]}],
            },
        ],
    }

    if object_type:
        record["referred_to_by"] = [{
            "type": "LinguisticObject",
            "content": object_type,
            "classified_as": [{"id": AAT_DESCRIPTION, "_label": "object type"}],
        }]

    if produced_by and (produced_by.get("carried_out_by") or produced_by.get("part")):
        record["produced_by"] = produced_by

    if img_src:
        record["representation"] = [{
            "type": "VisualItem",
            "digitally_shown_by": [{
                "type": "DigitalObject",
                "access_point": [{"id": img_src}],
                "format": "image/jpeg",
            }],
        }]

    record["subject_of"] = [{
        "type": "LinguisticObject",
        "digitally_carried_by": [{
            "type": "DigitalObject",
            "classified_as": [{"id": AAT_WEB_PAGE, "_label": "web page"}],
            "access_point": [{"id": uri}],
            "format": "text/html",
            "identified_by": [{"type": "Name", "content": "Rijksmuseum Boerhaave catalog page"}],
        }],
    }]

    return record


def main(html_file: Path, output_dir: Path):
    content = html_file.read_text(encoding="utf-8", errors="replace")
    parser = BoerhaaveParser()
    parser.feed(content)

    # Fallback: parse manually if the HTML parser gets confused
    records = parser.records
    if not records:
        print("HTML parser found no records, check the file encoding.")
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)
    written = 0
    for rec in records:
        accession = rec.get("accession", "").strip()
        if not accession:
            continue
        record = build_record(rec)
        out_path = output_dir / f"{accession}.json"
        out_path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  Wrote {out_path.name}  ({rec.get('title', '')[:60]})")
        written += 1

    print(f"Done: {written} records written to {output_dir}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python scripts/generate_boerhaave.py <html_file> <output_dir>")
        sys.exit(1)
    main(Path(sys.argv[1]), Path(sys.argv[2]))
