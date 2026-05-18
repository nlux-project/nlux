import os
import json

AI_RESEARCH_CONCEPT = "9df7d6d7-88d5-48fd-81f7-8f12dc2d43bb"


def _is_ai_research_note(note: dict) -> bool:
    for classification in note.get("classified_as", []):
        classification_id = classification.get("id", "")
        if (
            classification_id.endswith(f"data/concept/{AI_RESEARCH_CONCEPT}")
            or classification.get("_label") == "AI Research Analysis"
        ):
            return True
    return False


def text_value(value) -> str:
    """Return a stable text representation for values stored in SQL text columns."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = [text_value(item) for item in value]
        return " ".join(part for part in parts if part)
    if isinstance(value, dict):
        for key in ("content", "_label", "label", "value", "id", "@id"):
            if key in value:
                text = text_value(value.get(key))
                if text:
                    return text
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def extract_search_text(doc: dict) -> str:
    """Concatenate searchable record text for FTS indexing."""
    parts = []
    include_ai = os.getenv("NLUX_INDEX_AI_ENRICHMENT", "").lower() in {"1", "true", "yes"}
    if label := text_value(doc.get("_label")):
        parts.append(label)
    for item in doc.get("identified_by", []):
        if c := text_value(item.get("content")):
            parts.append(c)
    for item in doc.get("referred_to_by", []):
        if _is_ai_research_note(item) and not include_ai:
            continue
        if c := text_value(item.get("content")):
            parts.append(c)
    return " ".join(parts)
