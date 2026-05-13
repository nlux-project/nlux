import copy

from pipeline.process.base.mapper import Mapper


RMA_LABEL = "Rijksmuseum Amsterdam"
RMA_COLLECTION_LABEL = "Rijksmuseum Amsterdam"


def _language_code(language):
    if isinstance(language, dict):
        lang_id = language.get("id", "")
        if lang_id.endswith("300388277"):
            return "en"
        if lang_id.endswith("300388256"):
            return "nl"
    return None


def _notation_label(node):
    values = []
    for notation in node.get("notation", []) or []:
        if not isinstance(notation, dict):
            continue
        value = notation.get("@value")
        if value:
            values.append((_language_code({"id": notation.get("@language", "")}) or notation.get("@language"), value))
    for preferred in ("en", "nl"):
        for lang, value in values:
            if lang == preferred:
                return value
    return values[0][1] if values else None


def _identified_by_label(node):
    values = []
    for identifier in node.get("identified_by", []) or []:
        if not isinstance(identifier, dict):
            continue
        content = identifier.get("content")
        if content:
            languages = identifier.get("language") or []
            lang = _language_code(languages[0]) if languages else None
            values.append((lang, content))
    for preferred in ("en", "nl"):
        for lang, value in values:
            if lang == preferred:
                return value
    return values[0][1] if values else None


def _best_label(node):
    if not isinstance(node, dict):
        return None
    return node.get("_label") or _notation_label(node) or _identified_by_label(node) or node.get("content")


def _normalize_equivalents(data):
    equivalents = []
    for equivalent in data.get("equivalent", []) or []:
        if isinstance(equivalent, str):
            equivalents.append({"id": equivalent, "type": data.get("type", "HumanMadeObject"), "_label": data.get("_label", "Equivalent")})
        elif isinstance(equivalent, dict) and equivalent.get("id"):
            equivalent.setdefault("type", data.get("type", "HumanMadeObject"))
            equivalent.setdefault("_label", data.get("_label", "Equivalent"))
            equivalents.append(equivalent)
    data["equivalent"] = equivalents


def _walk_labels(node):
    if isinstance(node, dict):
        label = _best_label(node)
        if label and not node.get("_label"):
            node["_label"] = label
        for value in node.values():
            _walk_labels(value)
    elif isinstance(node, list):
        for value in node:
            _walk_labels(value)


def _has_supported_type(node_type, ok_types):
    if isinstance(node_type, list):
        return False
    return node_type in ok_types


def _drop_unsupported_reference_ids(node, ok_types, top=False):
    if isinstance(node, dict):
        node_type = node.get("type")
        if not top and node.get("id") and node_type and not _has_supported_type(node_type, ok_types):
            del node["id"]
        for key, value in node.items():
            if key in ["equivalent", "access_point", "conforms_to"]:
                continue
            _drop_unsupported_reference_ids(value, ok_types)
    elif isinstance(node, list):
        for value in node:
            _drop_unsupported_reference_ids(value, ok_types)


class RmaMapper(Mapper):
    def __init__(self, config):
        Mapper.__init__(self, config)
        self.namespace = config["namespace"]
        self.owner_label = config.get("ownerLabel", RMA_LABEL)
        self.collection_label = config.get("collectionLabel", RMA_COLLECTION_LABEL)

    def fix_identifier(self, identifier):
        return str(identifier or "").strip().rstrip("/").rsplit("/", 1)[-1]

    def post_reconcile(self, record):
        super().post_reconcile(record)
        _drop_unsupported_reference_ids(record.get("data"), getattr(self.configs, "ok_record_types", {}), top=True)

    def transform(self, record, rectype=None, reference=False):
        rec = record.get("data", {})
        if isinstance(rec, dict) and "data" in rec:
            rec = rec["data"]

        record_id = self.fix_identifier(rec.get("id", ""))
        if not record_id:
            return None

        data = copy.deepcopy(rec)
        data["id"] = f"{self.namespace}{record_id}"
        data.setdefault("type", "HumanMadeObject")
        data["_label"] = _best_label(data) or record_id
        data.setdefault("current_owner", [{"type": "Group", "_label": self.owner_label}])
        data.setdefault("member_of", []).append({"type": "Set", "_label": self.collection_label})
        _normalize_equivalents(data)
        _walk_labels(data)
        _drop_unsupported_reference_ids(data, getattr(self.configs, "ok_record_types", {}), top=True)

        return {"identifier": record_id, "data": data, "source": "rma"}
