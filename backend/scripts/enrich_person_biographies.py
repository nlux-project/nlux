#!/usr/bin/env python3
"""
Enrich Person records with short biographies from Wikidata/Wikipedia.

Run after loading records and generating agents:

    python scripts/enrich_person_biographies.py

The script updates API database records in place. It first reuses existing
Wikidata equivalents when present; otherwise it searches Wikidata by label.
Wikipedia page summaries are stored as Linked Art referred_to_by notes
classified as Display Biography so the lux-frontend Biography/Notes area can
render them without frontend changes.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).parent.parent))

WIKIDATA_ENTITY = "http://www.wikidata.org/entity/"
WIKIDATA_API = "https://www.wikidata.org/w/api.php"
WIKIDATA_ENTITY_DATA = "https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"
WIKIPEDIA_SUMMARY = "https://{lang}.wikipedia.org/api/rest_v1/page/summary/{title}"
USER_AGENT = "NLUX biography enrichment/0.1 (https://github.com/nlux-project/nlux)"

BIOGRAPHY_CONCEPT = "54e35d81-9548-4b4e-8973-de02b09bf9da"
AAT_DISPLAY_BIOGRAPHY = "http://vocab.getty.edu/aat/300080102"
AAT_WEB_PAGE = "http://vocab.getty.edu/aat/300264578"
AAT_LANG_EN = "http://vocab.getty.edu/aat/300388277"
AAT_LANG_NL = "http://vocab.getty.edu/aat/300388256"

LANGUAGE_AATS = {
    "en": ("english-language", "English", AAT_LANG_EN),
    "nl": ("dutch-language", "Dutch", AAT_LANG_NL),
}


def api_base() -> str:
    from app.config import settings

    return (
        (settings.base_url.rstrip("/") + "/")
        if settings.base_url
        else "http://localhost:8000/"
    )


def request_json(
    url: str,
    params: dict[str, str] | None = None,
    timeout: int = 20,
) -> dict:
    if params:
        url = f"{url}?{urlencode(params)}"
    request = Request(
        url,
        headers={"Accept": "application/json", "User-Agent": USER_AGENT},
    )
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def normalise_label(label: str) -> str:
    label = label.lower()
    label = re.sub(r"\([^)]*\)", "", label)
    label = re.sub(r"[^\w]+", " ", label)
    return re.sub(r"\s+", " ", label).strip()


def label_variants(label: str) -> list[str]:
    variants = [label.strip()]
    if "," in label:
        surname, rest = [part.strip() for part in label.split(",", 1)]
        if surname and rest:
            variants.append(f"{rest} {surname}")
    seen: set[str] = set()
    return [
        variant
        for variant in variants
        if not (variant.lower() in seen or seen.add(variant.lower()))
    ]


def wikidata_id_from_record(doc: dict) -> str | None:
    for equivalent in doc.get("equivalent", []):
        uri = equivalent.get("id", "")
        if WIKIDATA_ENTITY in uri:
            return uri.rstrip("/").rsplit("/", 1)[-1]
    return None


def _claim_ids(entity: dict, prop: str) -> list[str]:
    claims = entity.get("claims", {}).get(prop, [])
    ids = []
    for claim in claims:
        value = (
            claim.get("mainsnak", {})
            .get("datavalue", {})
            .get("value", {})
            .get("id")
        )
        if value:
            ids.append(value)
    return ids


def is_human(entity: dict) -> bool:
    return "Q5" in _claim_ids(entity, "P31")


def fetch_wikidata_entity(qid: str) -> dict | None:
    data = request_json(WIKIDATA_ENTITY_DATA.format(qid=qid))
    return data.get("entities", {}).get(qid)


def search_wikidata(label: str, languages: list[str]) -> tuple[str | None, dict | None]:
    wanted = {normalise_label(variant) for variant in label_variants(label)}
    candidates: list[str] = []

    for variant in label_variants(label):
        for language in languages:
            data = request_json(
                WIKIDATA_API,
                {
                    "action": "wbsearchentities",
                    "format": "json",
                    "language": language,
                    "uselang": language,
                    "type": "item",
                    "limit": "8",
                    "search": variant,
                },
            )
            candidates.extend(
                item["id"] for item in data.get("search", []) if item.get("id")
            )

    for qid in dict.fromkeys(candidates):
        entity = fetch_wikidata_entity(qid)
        if not entity or not is_human(entity):
            continue
        labels = {
            normalise_label(value.get("value", ""))
            for value in entity.get("labels", {}).values()
        }
        aliases = {
            normalise_label(alias.get("value", ""))
            for values in entity.get("aliases", {}).values()
            for alias in values
        }
        if wanted & (labels | aliases):
            return qid, entity

    return None, None


def wikipedia_sitelink(entity: dict, languages: list[str]) -> tuple[str, str] | None:
    sitelinks = entity.get("sitelinks", {})
    for language in languages:
        site = f"{language}wiki"
        link = sitelinks.get(site)
        if link and link.get("title"):
            return language, link["title"]
    return None


def fetch_wikipedia_summary(language: str, title: str) -> dict | None:
    data = request_json(WIKIPEDIA_SUMMARY.format(lang=language, title=quote(title)))
    extract = data.get("extract", "").strip()
    if not extract:
        return None
    return {
        "extract": extract,
        "page_url": data.get("content_urls", {}).get("desktop", {}).get("page"),
        "title": data.get("title") or title,
        "language": language,
    }


def has_biography_note(doc: dict) -> bool:
    for note in doc.get("referred_to_by", []):
        for classification in note.get("classified_as", []):
            if (
                classification.get("id", "").endswith(f"data/concept/{BIOGRAPHY_CONCEPT}")
                or classification.get("_label") == "Display Biography"
            ):
                return True
    return False


def biography_note(summary: dict, base: str) -> dict:
    language_code = summary["language"]
    slug, label, aat = LANGUAGE_AATS.get(language_code, LANGUAGE_AATS["en"])
    note = {
        "type": "LinguisticObject",
        "content": summary["extract"],
        "classified_as": [
            {
                "id": f"{base}data/concept/{BIOGRAPHY_CONCEPT}",
                "type": "Type",
                "_label": "Display Biography",
                "equivalent": [
                    {
                        "id": AAT_DISPLAY_BIOGRAPHY,
                        "type": "Type",
                        "_label": "biographies (documents)",
                    }
                ],
            }
        ],
        "language": [
            {
                "id": f"{base}data/concept/{slug}",
                "type": "Language",
                "_label": label,
                "equivalent": [{"id": aat, "type": "Language", "_label": label}],
            }
        ],
        "identified_by": [
            {"type": "Name", "content": f"Wikipedia summary: {summary['title']}"}
        ],
    }

    if summary.get("page_url"):
        note["subject_of"] = [
            {
                "type": "LinguisticObject",
                "digitally_carried_by": [
                    {
                        "type": "DigitalObject",
                        "classified_as": [
                            {
                                "id": AAT_WEB_PAGE,
                                "type": "Type",
                                "_label": "web page",
                            }
                        ],
                        "access_point": [{"id": summary["page_url"]}],
                        "format": "text/html",
                    }
                ],
            }
        ]

    return note


def add_equivalent(doc: dict, uri: str, label: str | None = None) -> None:
    equivalents = doc.setdefault("equivalent", [])
    if any(equivalent.get("id") == uri for equivalent in equivalents):
        return
    equivalent: dict[str, str] = {"id": uri, "type": doc.get("type", "Person")}
    if label:
        equivalent["_label"] = label
    equivalents.append(equivalent)


def enrich_person_record(
    doc: dict,
    languages: list[str],
    force: bool = False,
) -> tuple[dict, str | None]:
    if not force and has_biography_note(doc):
        return doc, None

    qid = wikidata_id_from_record(doc)
    entity = fetch_wikidata_entity(qid) if qid else None
    if entity and not is_human(entity):
        entity = None
    if not entity:
        label = doc.get("_label", "").strip()
        if not label:
            return doc, None
        qid, entity = search_wikidata(label, languages)
    if not qid or not entity:
        return doc, None

    link = wikipedia_sitelink(entity, languages)
    if not link:
        return doc, None

    summary = fetch_wikipedia_summary(*link)
    if not summary:
        return doc, None

    if force:
        doc["referred_to_by"] = [
            note
            for note in doc.get("referred_to_by", [])
            if not has_biography_note({"referred_to_by": [note]})
        ]

    doc.setdefault("referred_to_by", []).append(biography_note(summary, api_base()))
    add_equivalent(
        doc,
        f"{WIKIDATA_ENTITY}{qid}",
        entity.get("labels", {}).get("en", {}).get("value"),
    )
    if summary.get("page_url"):
        add_equivalent(doc, summary["page_url"], summary["title"])
    return doc, qid


def rebuild_fts_if_needed() -> None:
    from sqlalchemy import text

    from app.config import settings
    from app.database import engine

    if settings.database_url.startswith("sqlite"):
        with engine.connect() as conn:
            conn.execute(text("INSERT INTO records_fts(records_fts) VALUES('rebuild')"))
            conn.commit()


def run(
    record_id: str | None,
    limit: int | None,
    languages: list[str],
    force: bool,
    dry_run: bool,
) -> None:
    from app.database import SessionLocal
    from app.models import Record
    from scripts.load_data import extract_search_text

    db = SessionLocal()
    checked = enriched = skipped = errors = 0
    try:
        query = db.query(Record).filter(Record.type == "Person")
        if record_id:
            query = query.filter(Record.uri == record_id)

        for record in query.yield_per(100):
            if limit is not None and checked >= limit:
                break
            checked += 1
            try:
                doc = json.loads(record.data)
                updated, qid = enrich_person_record(doc, languages, force=force)
                if qid is None:
                    skipped += 1
                    continue
                enriched += 1
                print(f"Enriched {record.label or record.uri} from Wikidata {qid}")
                if not dry_run:
                    raw = json.dumps(updated, ensure_ascii=False)
                    record.data = raw
                    record.search_text = extract_search_text(updated)
                    record.label = updated.get("_label", record.label)
                time.sleep(0.1)
            except Exception as exc:
                errors += 1
                print(f"ERROR {record.uri}: {exc}")

        if not dry_run:
            db.commit()
            if enriched:
                rebuild_fts_if_needed()
        print(
            f"Done: checked={checked} enriched={enriched} "
            f"skipped={skipped} errors={errors}"
        )
    finally:
        db.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record-id", help="Only enrich one Person record URI")
    parser.add_argument("--limit", type=int, help="Maximum number of Person records to inspect")
    parser.add_argument(
        "--languages",
        default="nl,en",
        help="Comma-separated Wikipedia language preference order, default: nl,en",
    )
    parser.add_argument("--force", action="store_true", help="Replace existing Display Biography notes")
    parser.add_argument("--dry-run", action="store_true", help="Fetch and report matches without writing")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run(
        record_id=args.record_id,
        limit=args.limit,
        languages=[lang.strip() for lang in args.languages.split(",") if lang.strip()],
        force=args.force,
        dry_run=args.dry_run,
    )
