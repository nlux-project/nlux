#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

DATA_PIPELINE_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(DATA_PIPELINE_ROOT))

from pipeline.process.ai_enrichment import (  # noqa: E402
    DEFAULT_MODEL,
    DEFAULT_PROMPT_VERSION,
    AIEnrichmentError,
    catalog_snapshot,
    dry_run_response,
    error_sidecar_record,
    load_prompt_template,
    request_provider,
    sidecar_record,
)

CHECKLIST_RE = re.compile(r"^(?P<prefix>\s*)\[(?P<mark>[ xX])\]\s+(?P<object_id>\S+)(?P<suffix>.*)$")


@dataclass
class ChecklistItem:
    line_no: int
    object_id: str
    done: bool


def parse_checklist(text: str) -> list[ChecklistItem]:
    items = []
    for line_no, line in enumerate(text.splitlines(), 1):
        match = CHECKLIST_RE.match(line)
        if not match:
            continue
        items.append(
            ChecklistItem(
                line_no=line_no,
                object_id=match.group("object_id"),
                done=match.group("mark").upper() == "X",
            )
        )
    return items


def mark_checklist_done(text: str, completed: set[str]) -> str:
    lines = text.splitlines(keepends=True)
    for index, line in enumerate(lines):
        line_ending = "\n" if line.endswith("\n") else ""
        body = line[:-1] if line_ending else line
        match = CHECKLIST_RE.match(body)
        if match and match.group("object_id") in completed:
            lines[index] = f"{match.group('prefix')}[X] {match.group('object_id')}{match.group('suffix')}{line_ending}"
    return "".join(lines)


def api_record_url(base_url: str, object_id: str) -> str:
    if object_id.startswith("http://") or object_id.startswith("https://"):
        return object_id
    return f"{base_url.rstrip('/')}/data/object/{quote(object_id.strip(), safe='')}"


def fetch_json(url: str, timeout: int = 60) -> dict[str, Any]:
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "NLUX AI Enrichment/0.1"})
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def nested_ids(value: Any, key: str) -> list[str]:
    ids = []
    for item in as_list(value):
        if isinstance(item, dict):
            item_id = item.get(key)
            if isinstance(item_id, str):
                ids.append(item_id)
    return ids


def extract_iiif_manifest_urls(record: dict[str, Any]) -> list[str]:
    urls: list[str] = []
    for subject in as_list(record.get("subject_of")):
        if not isinstance(subject, dict):
            continue
        for digital in as_list(subject.get("digitally_carried_by")):
            if not isinstance(digital, dict):
                continue
            urls.extend(nested_ids(digital.get("access_point"), "id"))
    return [url for url in dict.fromkeys(urls) if "iiif/manifest" in url or "iiif.io/api/presentation" in url]


def extract_image_urls(record: dict[str, Any]) -> list[str]:
    urls: list[str] = []
    for representation in as_list(record.get("representation")):
        if not isinstance(representation, dict):
            continue
        for digital in as_list(representation.get("digitally_shown_by")):
            if not isinstance(digital, dict):
                continue
            urls.extend(nested_ids(digital.get("access_point"), "id"))
            if isinstance(digital.get("id"), str):
                urls.append(digital["id"])
    return list(dict.fromkeys(urls))


def extract_web_pages(record: dict[str, Any]) -> list[str]:
    urls: list[str] = []
    for subject in as_list(record.get("subject_of")):
        if not isinstance(subject, dict):
            continue
        for digital in as_list(subject.get("digitally_carried_by")):
            if not isinstance(digital, dict):
                continue
            for url in nested_ids(digital.get("access_point"), "id"):
                if "iiif/manifest" not in url and "iiif.io/api/presentation" not in url:
                    urls.append(url)
    for equivalent in as_list(record.get("equivalent")):
        if isinstance(equivalent, dict) and isinstance(equivalent.get("id"), str):
            urls.append(equivalent["id"])
    return list(dict.fromkeys(urls))


def fetch_manifest_summaries(urls: list[str], timeout: int) -> list[dict[str, Any]]:
    summaries = []
    for url in urls:
        try:
            manifest = fetch_json(url, timeout=timeout)
        except Exception as exc:
            summaries.append({"url": url, "error": str(exc)})
            continue
        summaries.append(
            {
                "url": url,
                "id": manifest.get("id") or manifest.get("@id"),
                "label": manifest.get("label"),
                "type": manifest.get("type") or manifest.get("@type"),
                "summary": manifest.get("summary"),
            }
        )
    return summaries


def collection_from_record(record: dict[str, Any]) -> str:
    for member_of in as_list(record.get("member_of")):
        if isinstance(member_of, dict):
            label = member_of.get("_label") or member_of.get("id")
            if label:
                return str(label)
    return "Unknown collection"


def object_id_from_url_or_record(input_id: str, record: dict[str, Any]) -> str:
    record_id = record.get("id") or record.get("@id") or input_id
    parsed = urlparse(record_id)
    if parsed.path:
        return parsed.path.rstrip("/").split("/")[-1]
    return str(record_id)


def render_research_prompt(
    template: str,
    record: dict[str, Any],
    object_id: str,
    prompt_version: str,
    api_url: str,
    image_urls: list[str],
    manifest_urls: list[str],
    manifest_summaries: list[dict[str, Any]],
) -> str:
    payload = {
        "prompt_version": prompt_version,
        "record_url": api_url,
        "record_json": record,
        "catalog_snapshot": catalog_snapshot(record),
        "image_urls": image_urls,
        "iiif_manifest_urls": manifest_urls,
        "iiif_manifests": manifest_summaries,
    }
    replacements = {
        "NLUX_OBJECT_ID": object_id,
        "NLUX_COLLECTION": collection_from_record(record),
        "prompt_version": prompt_version,
        "record_url": api_url,
        "record_json": json.dumps(record, indent=2, ensure_ascii=False, sort_keys=True),
        "research_payload": json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True),
    }
    prompt = template
    for key, value in replacements.items():
        prompt = prompt.replace("{" + key + "}", str(value))
    if "{research_payload}" not in template:
        prompt = f"{prompt.rstrip()}\n\n## NLUX API payload\n```json\n{replacements['research_payload']}\n```\n"
    return prompt


def markdown_report(sidecar: dict[str, Any], api_url: str) -> str:
    lines = [
        f"# AI enrichment for {sidecar['catalog_snapshot'].get('label') or sidecar['record_id']}",
        "",
        f"- Record: [{sidecar['record_id']}]({api_url})",
        f"- Status: {sidecar['status']}",
        f"- Generated: {sidecar['generated_at']}",
        f"- Model: {sidecar['model']}",
        f"- Prompt: {sidecar['prompt_version']}",
        "",
    ]
    if sidecar.get("summary"):
        lines.extend(["## Summary", "", str(sidecar["summary"]), ""])
    findings = sidecar.get("findings") or []
    if findings:
        lines.extend(["## Findings", ""])
        for finding in findings:
            title = finding.get("title") or finding.get("issue") or "Finding"
            severity = finding.get("severity", "info")
            confidence = finding.get("confidence")
            lines.append(f"### {title}")
            lines.append("")
            lines.append(f"- Severity: {severity}")
            if confidence:
                lines.append(f"- Confidence: {confidence}")
            detail = finding.get("detail") or finding.get("description")
            if detail:
                lines.extend(["", str(detail)])
            lines.append("")
    sources = sidecar.get("sources") or []
    if sources:
        lines.extend(["## Sources", ""])
        for source in sources:
            if isinstance(source, dict):
                title = source.get("title") or source.get("label") or source.get("url") or "Source"
                url = source.get("url")
                lines.append(f"- [{title}]({url})" if url else f"- {title}")
            else:
                lines.append(f"- {source}")
        lines.append("")
    if sidecar.get("error"):
        lines.extend(["## Error", "", str(sidecar["error"]), ""])
    return "\n".join(lines)


def write_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")))
        fh.write("\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate AI enrichment sidecar records for selected NLUX objects.")
    parser.add_argument("checklist", help="Checklist file with lines like '[ ] object-id' and '[X] object-id'.")
    parser.add_argument("--api-base", default="http://localhost:8000", help="NLUX API base URL.")
    parser.add_argument("--prompt", default=str(Path(__file__).with_name("prompt.md")), help="Prompt template path.")
    parser.add_argument("--output-jsonl", default="data/output/ai-enrichment/results.jsonl", help="Sidecar JSONL output path.")
    parser.add_argument("--reports-dir", default="data/output/ai-enrichment/reports", help="Markdown report output directory.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Provider model name.")
    parser.add_argument("--prompt-version", default=DEFAULT_PROMPT_VERSION, help="Prompt version label.")
    parser.add_argument("--source", default="nlux-ai-enrichment", help="Source label stored in sidecar output.")
    parser.add_argument("--dry-run", action="store_true", help="Do not call an AI provider; write a placeholder sidecar.")
    parser.add_argument("--no-mark-done", action="store_true", help="Do not update checklist items after successful enrichment.")
    parser.add_argument("--include-done", action="store_true", help="Reprocess checklist items already marked done.")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of records to process.")
    parser.add_argument("--timeout", type=int, default=120, help="HTTP timeout in seconds.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    checklist_path = Path(args.checklist)
    checklist_text = checklist_path.read_text(encoding="utf-8")
    items = parse_checklist(checklist_text)
    if not items:
        print(f"No checklist items found in {checklist_path}", file=sys.stderr)
        return 1

    pending = [item for item in items if args.include_done or not item.done]
    if args.limit is not None:
        pending = pending[: args.limit]
    if not pending:
        print("No pending records.")
        return 0

    prompt_template = load_prompt_template(args.prompt)
    output_jsonl = Path(args.output_jsonl)
    reports_dir = Path(args.reports_dir)
    completed: set[str] = set()

    for item in pending:
        api_url = api_record_url(args.api_base, item.object_id)
        print(f"Fetching {api_url}")
        try:
            record = fetch_json(api_url, timeout=args.timeout)
            object_id = object_id_from_url_or_record(item.object_id, record)
            image_urls = extract_image_urls(record)
            manifest_urls = extract_iiif_manifest_urls(record)
            manifest_summaries = fetch_manifest_summaries(manifest_urls, args.timeout)
            prompt = render_research_prompt(
                prompt_template,
                record,
                object_id,
                args.prompt_version,
                api_url,
                image_urls,
                manifest_urls,
                manifest_summaries,
            )
            if args.dry_run:
                analysis = dry_run_response(record)
                status = "skipped"
            else:
                analysis = request_provider(prompt, args.model, timeout=args.timeout)
                status = "ok"
            sidecar = sidecar_record(record, args.source, args.model, args.prompt_version, analysis, status=status)
            if sidecar["status"] == "ok":
                completed.add(item.object_id)
        except (HTTPError, URLError, TimeoutError, AIEnrichmentError, json.JSONDecodeError) as exc:
            fallback_record = {"id": api_url, "type": "HumanMadeObject", "_label": item.object_id}
            sidecar = error_sidecar_record(fallback_record, args.source, args.model, args.prompt_version, exc)
            print(f"ERROR {item.object_id}: {exc}", file=sys.stderr)
        except Exception as exc:
            fallback_record = {"id": api_url, "type": "HumanMadeObject", "_label": item.object_id}
            sidecar = error_sidecar_record(fallback_record, args.source, args.model, args.prompt_version, exc)
            print(f"ERROR {item.object_id}: {exc}", file=sys.stderr)

        write_jsonl(output_jsonl, sidecar)
        report_slug = quote(object_id_from_url_or_record(item.object_id, {"id": sidecar["record_id"]}), safe="")
        report_name = f"{report_slug}.md"
        reports_dir.mkdir(parents=True, exist_ok=True)
        (reports_dir / report_name).write_text(markdown_report(sidecar, api_url), encoding="utf-8")
        print(f"Wrote {sidecar['status']} sidecar for {sidecar['record_id']}")

    if completed and not args.no_mark_done:
        checklist_path.write_text(mark_checklist_done(checklist_text, completed), encoding="utf-8")
        print(f"Marked {len(completed)} checklist item(s) done.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
