from __future__ import annotations

import datetime as _dt
import html
import json
import os
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

AI_RESEARCH_CONCEPT = "9df7d6d7-88d5-48fd-81f7-8f12dc2d43bb"
AI_RESEARCH_LABEL = "AI Research Analysis"
AI_RESEARCH_TYPE_URI = "https://nlux.local/data/concept/ai-research-analysis"
DEFAULT_PROMPT_VERSION = "ai-research-v1"
DEFAULT_MODEL = "nlux-ai-research-dry-run"

VALID_STATUSES = {"ok", "skipped", "error"}
VALID_FINDING_SEVERITIES = {"major", "minor", "info"}
REQUIRED_SIDECAR_FIELDS = {
    "record_id",
    "source",
    "generated_at",
    "model",
    "prompt_version",
    "summary",
    "catalog_snapshot",
    "findings",
    "sources",
    "status",
}


class AIEnrichmentError(ValueError):
    pass


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def record_label(record: dict[str, Any]) -> str:
    if record.get("_label"):
        return str(record["_label"])
    for identifier in as_list(record.get("identified_by")):
        if isinstance(identifier, dict) and identifier.get("content"):
            return str(identifier["content"])
    return record.get("id") or record.get("@id") or "Untitled record"


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _contents(values: list[Any]) -> list[str]:
    contents = []
    for value in values:
        if isinstance(value, dict) and value.get("content"):
            contents.append(str(value["content"]))
    return contents


def catalog_snapshot(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": record.get("id") or record.get("@id"),
        "type": record.get("type"),
        "label": record_label(record),
        "identifiers": _contents(as_list(record.get("identified_by"))),
        "notes": _contents(as_list(record.get("referred_to_by"))),
        "classifications": [
            item.get("_label") or item.get("id")
            for item in as_list(record.get("classified_as"))
            if isinstance(item, dict)
        ],
    }


def summarize_record(record: dict[str, Any]) -> dict[str, Any]:
    snapshot = catalog_snapshot(record)
    return {
        "id": snapshot["id"],
        "type": snapshot["type"],
        "label": snapshot["label"],
        "catalog_snapshot": snapshot,
    }


def render_prompt(record: dict[str, Any], template: str, prompt_version: str) -> str:
    summary = summarize_record(record)
    return template.format(
        prompt_version=prompt_version,
        record_json=json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True),
    )


def default_prompt_template() -> str:
    return (
        "You are researching a cultural heritage collection record.\n"
        "Prompt version: {prompt_version}\n\n"
        "Return JSON with keys summary, catalog_snapshot, findings, sources, raw_response_ref.\n"
        "Findings must describe corrections or additions without overwriting catalog fields.\n\n"
        "Record:\n{record_json}\n"
    )


def load_prompt_template(path: str | None) -> str:
    if not path:
        default_path = Path(__file__).parent / "prompt_templates" / f"{DEFAULT_PROMPT_VERSION}.txt"
        if default_path.exists():
            return default_path.read_text(encoding="utf-8")
        return default_prompt_template()
    return Path(path).read_text(encoding="utf-8")


def dry_run_response(record: dict[str, Any]) -> dict[str, Any]:
    snapshot = catalog_snapshot(record)
    return {
        "summary": f"AI enrichment was not run. Dry-run prompt prepared for {snapshot['label']}.",
        "catalog_snapshot": snapshot,
        "findings": [],
        "sources": [],
        "raw_response_ref": None,
    }


def _openai_payload(prompt: str, model: str) -> dict[str, Any]:
    return {
        "model": model,
        "input": prompt,
        "text": {"format": {"type": "json_object"}},
    }


def _generic_payload(prompt: str, model: str) -> dict[str, Any]:
    return {"model": model, "prompt": prompt}


def _response_text(data: dict[str, Any]) -> str | None:
    text = data.get("output_text")
    if isinstance(text, str) and text.strip():
        return text
    for item in as_list(data.get("output")):
        if not isinstance(item, dict):
            continue
        for content in as_list(item.get("content")):
            if not isinstance(content, dict):
                continue
            text = content.get("text")
            if isinstance(text, str) and text.strip():
                return text
    return None


def _parse_provider_response(data: dict[str, Any], endpoint: str) -> dict[str, Any]:
    if isinstance(data.get("analysis"), dict):
        return data["analysis"]
    if "api.openai.com/v1/responses" in endpoint:
        text = _response_text(data)
        if not text:
            raise AIEnrichmentError("OpenAI response did not include output text")
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise AIEnrichmentError(f"OpenAI response output was not valid JSON: {exc}") from exc
    return data


def _http_error_detail(exc: HTTPError) -> str:
    try:
        body = exc.read().decode("utf-8")
    except Exception:
        return ""
    if not body:
        return ""
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return body.strip()
    error = data.get("error") if isinstance(data, dict) else None
    if isinstance(error, dict):
        parts = [
            str(error.get(key))
            for key in ("message", "type", "code")
            if error.get(key)
        ]
        return " | ".join(parts)
    return body.strip()


def _provider_http_error(endpoint: str, exc: HTTPError) -> AIEnrichmentError:
    detail = _http_error_detail(exc)
    suffix = f": {detail}" if detail else ""
    if "api.openai.com/v1/responses" in endpoint:
        if exc.code == 429:
            return AIEnrichmentError(
                f"OpenAI provider request failed with HTTP 429{suffix}. "
                "Check project billing/quota, rate limits, and model access."
            )
        return AIEnrichmentError(f"OpenAI provider request failed with HTTP {exc.code}{suffix}.")
    if endpoint.rstrip("/") in {"http://localhost:8000", "http://127.0.0.1:8000"}:
        return AIEnrichmentError(
            f"Provider request to {endpoint} failed with HTTP {exc.code}{suffix}. "
            "NLUX_AI_ENRICH_ENDPOINT must be an AI provider endpoint, not the NLUX data API base URL."
        )
    return AIEnrichmentError(f"Provider request to {endpoint} failed with HTTP {exc.code}{suffix}.")


def request_provider(prompt: str, model: str, timeout: int = 120) -> dict[str, Any]:
    endpoint = os.getenv("NLUX_AI_ENRICH_ENDPOINT")
    api_key = os.getenv("NLUX_AI_ENRICH_API_KEY")
    if not endpoint:
        raise AIEnrichmentError(
            "NLUX_AI_ENRICH_ENDPOINT is not set. Use --dry-run or configure a provider endpoint."
        )

    payload_dict = (
        _openai_payload(prompt, model)
        if "api.openai.com/v1/responses" in endpoint
        else _generic_payload(prompt, model)
    )
    payload = json.dumps(payload_dict).encode("utf-8")
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    request = Request(endpoint, data=payload, headers=headers, method="POST")
    try:
        with urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise _provider_http_error(endpoint, exc) from exc
    except URLError as exc:
        raise AIEnrichmentError(f"Provider request to {endpoint} failed: {exc.reason}") from exc

    if isinstance(data, dict):
        return _parse_provider_response(data, endpoint)
    raise AIEnrichmentError("Provider returned a non-object JSON response")


def sidecar_record(
    record: dict[str, Any],
    source: str,
    model: str,
    prompt_version: str,
    analysis: dict[str, Any],
    status: str = "ok",
    error: str | None = None,
) -> dict[str, Any]:
    output = {
        "record_id": record.get("id") or record.get("@id"),
        "source": source,
        "generated_at": utc_now(),
        "model": model,
        "prompt_version": prompt_version,
        "summary": analysis.get("summary", ""),
        "catalog_snapshot": analysis.get("catalog_snapshot") or catalog_snapshot(record),
        "findings": analysis.get("findings", []),
        "sources": analysis.get("sources", []),
        "raw_response_ref": analysis.get("raw_response_ref"),
        "status": status,
    }
    if error:
        output["error"] = error
    validate_sidecar_record(output)
    return output


def error_sidecar_record(
    record: dict[str, Any],
    source: str,
    model: str,
    prompt_version: str,
    error: Exception,
) -> dict[str, Any]:
    return sidecar_record(
        record,
        source,
        model,
        prompt_version,
        {
            "summary": "",
            "catalog_snapshot": catalog_snapshot(record),
            "findings": [],
            "sources": [],
            "raw_response_ref": None,
        },
        status="error",
        error=str(error),
    )


def validate_sidecar_record(record: dict[str, Any]) -> None:
    missing = REQUIRED_SIDECAR_FIELDS - set(record)
    if missing:
        raise AIEnrichmentError(f"AI sidecar record missing required fields: {', '.join(sorted(missing))}")
    if not isinstance(record["record_id"], str) or not record["record_id"]:
        raise AIEnrichmentError("AI sidecar record requires a non-empty record_id")
    if record["status"] not in VALID_STATUSES:
        raise AIEnrichmentError(f"Invalid AI sidecar status: {record['status']}")
    if record["status"] == "ok" and not record["sources"]:
        raise AIEnrichmentError("AI sidecar ok records must include at least one source")
    if not isinstance(record["findings"], list):
        raise AIEnrichmentError("AI sidecar findings must be a list")
    if not isinstance(record["sources"], list):
        raise AIEnrichmentError("AI sidecar sources must be a list")
    for finding in record["findings"]:
        if not isinstance(finding, dict):
            raise AIEnrichmentError("AI sidecar findings must be objects")
        severity = finding.get("severity", "info")
        if severity not in VALID_FINDING_SEVERITIES:
            raise AIEnrichmentError(f"Invalid AI finding severity: {severity}")


def load_sidecar(path: Path) -> dict[str, dict[str, Any]]:
    records = {}
    files = [path] if path.is_file() else sorted(path.glob("*.jsonl"))
    for file_path in files:
        with file_path.open(encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, 1):
                if not line.strip():
                    continue
                record = json.loads(line)
                validate_sidecar_record(record)
                if record["status"] == "ok":
                    records[record["record_id"]] = record
    return records


def has_ai_research_note(record: dict[str, Any]) -> bool:
    for note in as_list(record.get("referred_to_by")):
        if not isinstance(note, dict):
            continue
        for classification in as_list(note.get("classified_as")):
            if (
                isinstance(classification, dict)
                and (
                    classification.get("id", "").endswith(f"data/concept/{AI_RESEARCH_CONCEPT}")
                    or classification.get("id") == AI_RESEARCH_TYPE_URI
                    or classification.get("_label") == AI_RESEARCH_LABEL
                )
            ):
                return True
    return False


def _source_label(source: dict[str, Any]) -> str:
    title = source.get("title") or source.get("label") or source.get("url") or "Source"
    url = source.get("url")
    if url:
        return f'<a href="{html.escape(str(url), quote=True)}">{html.escape(str(title))}</a>'
    return html.escape(str(title))


def ai_research_html(sidecar: dict[str, Any]) -> str:
    parts = ['<section class="nlux-ai-research">']
    if sidecar.get("summary"):
        parts.append(f"<p>{html.escape(str(sidecar['summary']))}</p>")

    findings = sidecar.get("findings", [])
    if findings:
        parts.append("<h3>Key findings</h3>")
        for severity in ("major", "minor", "info"):
            group = [f for f in findings if f.get("severity", "info") == severity]
            if not group:
                continue
            parts.append(f"<h4>{severity.title()}</h4><ul>")
            for finding in group:
                title = html.escape(str(finding.get("title") or finding.get("issue") or "Finding"))
                detail = html.escape(str(finding.get("detail") or finding.get("description") or ""))
                confidence = finding.get("confidence")
                confidence_text = f" Confidence: {html.escape(str(confidence))}." if confidence is not None else ""
                parts.append(f"<li><strong>{title}</strong>{': ' + detail if detail else ''}{confidence_text}</li>")
            parts.append("</ul>")

    snapshot = sidecar.get("catalog_snapshot") or {}
    if snapshot:
        parts.append("<h3>Catalog snapshot</h3><dl>")
        for key in ("label", "type"):
            if snapshot.get(key):
                parts.append(f"<dt>{html.escape(key.replace('_', ' ').title())}</dt><dd>{html.escape(str(snapshot[key]))}</dd>")
        parts.append("</dl>")

    sources = sidecar.get("sources", [])
    if sources:
        parts.append("<h3>Sources</h3><ul>")
        for source in sources:
            if isinstance(source, dict):
                parts.append(f"<li>{_source_label(source)}</li>")
            else:
                parts.append(f"<li>{html.escape(str(source))}</li>")
        parts.append("</ul>")

    meta = "Generated {date} with {model} ({prompt})".format(
        date=html.escape(str(sidecar.get("generated_at", ""))),
        model=html.escape(str(sidecar.get("model", ""))),
        prompt=html.escape(str(sidecar.get("prompt_version", ""))),
    )
    parts.append(f'<p class="nlux-ai-research-meta">{meta}</p>')
    parts.append("</section>")
    return "".join(parts)


def ai_research_note(sidecar: dict[str, Any], base_uri: str = "https://nlux.local/") -> dict[str, Any]:
    base = base_uri.rstrip("/") + "/"
    return {
        "type": "LinguisticObject",
        "content": sidecar.get("summary") or "AI research analysis",
        "_content_html": ai_research_html(sidecar),
        "classified_as": [
            {
                "id": f"{base}data/concept/{AI_RESEARCH_CONCEPT}",
                "type": "Type",
                "_label": AI_RESEARCH_LABEL,
                "equivalent": [
                    {
                        "id": AI_RESEARCH_TYPE_URI,
                        "type": "Type",
                        "_label": AI_RESEARCH_LABEL,
                    }
                ],
            }
        ],
        "identified_by": [{"type": "Name", "content": AI_RESEARCH_LABEL}],
    }


def merge_ai_enrichment(record: dict[str, Any], sidecar: dict[str, Any], base_uri: str = "https://nlux.local/") -> dict[str, Any]:
    if has_ai_research_note(record):
        return record
    merged = dict(record)
    merged["referred_to_by"] = list(as_list(record.get("referred_to_by")))
    merged["referred_to_by"].append(ai_research_note(sidecar, base_uri))
    return merged
