import html
import re


FIELD_MAP = {
    "Collectie": "collection",
    "Objectnaam": "object_name",
    "Titel": "titles",
    "Rubriek": "category",
    "Kunstenaar": "artist",
    "Datering": "dating",
    "Materiaal": "material",
    "Afmetingen": "dimensions",
    "Herkomst": "provenance",
    "Inventarisnummer": "inventory_number",
    "Andere nummers": "other_numbers",
    "Objectstatus": "object_status",
    "Copyright": "copyright",
    "Reproductie": "reproduction",
}


def _strip_tags(value):
    value = re.sub(r"<br\s*/?>", "\n", value, flags=re.I)
    value = re.sub(r"<[^>]+>", "", value)
    value = html.unescape(value)
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n+", "\n", value)
    return value.strip()


def _first_match(pattern, value, flags=0):
    match = re.search(pattern, value, flags)
    return match.group(1).strip() if match else None


def parse_record_html(record_html, objectid=None):
    """Parse the CollectionConnection rendered record HTML into a stable dict."""
    rendered = html.unescape(record_html or "")
    record = {}

    title = _first_match(r'<h3[^>]*class="panel-title"[^>]*>(.*?)<span', rendered, re.S)
    if title:
        record["titles"] = [_strip_tags(title)]

    image_dzi = _first_match(r'tileSources:\s*\[\s*"([^"]+)"', rendered, re.S)
    if image_dzi:
        record["image_dzi"] = html.unescape(image_dzi)

    deeplink = _first_match(r"<b>Deeplink:\s*</b>\s*(https?://[^<\s]+)", rendered, re.I)
    if deeplink:
        record["deeplink"] = html.unescape(deeplink)
        objectid = objectid or _first_match(r"objectid=([^&]+)", deeplink)

    if objectid:
        record["objectid"] = str(objectid)

    pattern = re.compile(
        r"<strong>\s*([^:<]+):\s*</strong>\s*<br\s*/?>\s*(.*?)(?=<br\s*/?>\s*<br\s*/?>\s*<strong>|<div><b>Deeplink:|$)",
        re.S | re.I,
    )
    for label, raw_value in pattern.findall(rendered):
        key = FIELD_MAP.get(_strip_tags(label))
        if not key:
            continue
        value = _strip_tags(raw_value)
        if not value:
            continue
        if key == "titles":
            record.setdefault("titles", [])
            if value not in record["titles"]:
                record["titles"].append(value)
        else:
            record[key] = value

    return record


def parse_search_response(payload):
    """Parse the ASP.NET JSON wrapper returned by ccConnector.asmx/search."""
    if isinstance(payload, dict) and "d" in payload:
        import json

        payload = json.loads(payload["d"])
    result = payload.get("result", "")
    objectid = payload.get("uniqueId")
    return parse_record_html(result, objectid=objectid)
