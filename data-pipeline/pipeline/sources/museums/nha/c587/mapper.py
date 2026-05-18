import base64
import re
from html import unescape
from urllib.parse import quote

from cromulent import model, vocab

from pipeline.process.base.mapper import Mapper


NHA_LABEL = "Noord-Hollands Archief"
NHA_COLLECTION_LABEL = "587 - portretten van de Provinciale Atlas Noord-Holland"
NHA_DETAIL_BASE = "https://noord-hollandsarchief.nl/beelden/beeldbank/detail/{record_id}"
IIIF_PRESENTATION_3_CONTEXT = "http://iiif.io/api/presentation/3/context.json"

DESCRIPTION_STATEMENT = "http://vocab.getty.edu/aat/300435416"


def _clean(value):
    if value is None:
        return None
    value = re.sub(r"<[^>]+>", " ", str(value))
    value = re.sub(r"\s+", " ", unescape(value)).strip()
    return value or None


def _values(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [_clean(item) for item in value if _clean(item)]
    cleaned = _clean(value)
    return [cleaned] if cleaned else []


def _metadata(record):
    return {
        item.get("field"): item.get("value")
        for item in record.get("metadata", [])
        if item.get("field")
    }


def _first(metadata, field):
    values = _values(metadata.get(field))
    return values[0] if values else None


def _api_base(config):
    all_configs = config.get("all_configs")
    internal_uri = getattr(all_configs, "internal_uri", "") if all_configs else ""
    if internal_uri:
        return internal_uri.rstrip("/").removesuffix("/data")
    return "http://localhost:8000"


def _iiif_token(url):
    return base64.urlsafe_b64encode(url.encode("utf-8")).decode("ascii").rstrip("=")


def _iiif_manifest_url(api_base, image_url, label):
    token = _iiif_token(image_url)
    return f"{api_base}/iiif/manifest/{token}?label={quote(label or 'Image')}"


def _append_iiif_manifest(data, manifest_url):
    if not manifest_url:
        return

    data.setdefault("subject_of", []).append(
        {
            "type": "LinguisticObject",
            "_label": "IIIF manifest",
            "digitally_carried_by": [
                {
                    "type": "DigitalObject",
                    "_label": "IIIF Presentation 3 manifest",
                    "format": "application/ld+json",
                    "conforms_to": [
                        {
                            "id": IIIF_PRESENTATION_3_CONTEXT,
                            "type": "InformationObject",
                            "_label": "IIIF Presentation API 3.0",
                        }
                    ],
                    "access_point": [
                        {
                            "id": manifest_url,
                            "type": "DigitalObject",
                        }
                    ],
                }
            ],
        }
    )


def _year_range(value):
    years = re.findall(r"\b(\d{3,4})\b", value or "")
    if not years:
        return None, None
    return years[0].zfill(4), years[-1].zfill(4)


def _creator_name(value):
    value = _clean(value)
    if not value:
        return None
    value = value.rstrip(",; ")
    if value.lower() == "anoniem":
        return None
    return value


def _person_name_from_portrait_title(title):
    title = _clean(title)
    if not title:
        return None

    match = re.match(
        r"^(?:zelfportret|self-?portrait)(?:\s+(?:van|of))?\s+(.+)$",
        title,
        flags=re.IGNORECASE,
    )
    if not match:
        match = re.match(
            r"^(?:portret|portrait)\s+(?:van|of)\s+(.+)$",
            title,
            flags=re.IGNORECASE,
        )
    if not match:
        return None

    name = re.split(r"\s*[;|]\s*", match.group(1), 1)[0]
    name = re.sub(r"\s*,?\s*(?:\(?\d{3,4}\b.*|\*.*)$", "", name).strip(" ,.;")
    return name or None


def _note(content, classification_uri=None, classification_label=None):
    note = model.LinguisticObject(content=content)
    if classification_uri or classification_label:
        note.classified_as = model.Type(ident=classification_uri, label=classification_label)
    return note


class NhaC587Mapper(Mapper):
    source_name = "nha-c587"
    owner_label = NHA_LABEL
    collection_label = NHA_COLLECTION_LABEL
    detail_base = NHA_DETAIL_BASE

    def __init__(self, config):
        Mapper.__init__(self, config)
        self.namespace = config["namespace"]
        self.api_base = _api_base(config)
        self.source_name = config.get("name", self.source_name)
        self.owner_label = config.get("ownerLabel", self.owner_label)
        self.collection_label = config.get("collectionLabel", self.collection_label)
        self.detail_base = config.get("detailBase", self.detail_base)

    def transform(self, record, rectype=None, reference=False):
        rec = record.get("data", {})
        if isinstance(rec, dict) and "data" in rec:
            rec = rec["data"]

        record_id = str(rec.get("id", ""))
        if not record_id:
            return None

        metadata = _metadata(rec)
        object_numbers = _values(metadata.get("nummer"))
        primary_title = (
            _first(metadata, "beschrijving")
            or _clean(rec.get("title"))
            or (object_numbers[0] if object_numbers else record_id)
        )

        uri = f"{self.namespace}{record_id}"
        top = model.HumanMadeObject(ident=uri, label=primary_title)

        if primary_title:
            top.identified_by = vocab.PrimaryName(content=primary_title)
        for object_number in object_numbers:
            top.identified_by = vocab.AccessionNumber(content=object_number)

        record_type = _first(metadata, "record_type")
        if record_type:
            top.classified_as = model.Type(label=record_type)

        description = _first(metadata, "beschrijving") or _clean(rec.get("description"))
        if description and description != primary_title:
            top.referred_to_by = _note(description, DESCRIPTION_STATEMENT, "description")

        for note_field in ("opmerkingen", "literatuur", "toestemming"):
            for note in _values(metadata.get(note_field)):
                top.referred_to_by = model.LinguisticObject(content=note)

        for person in _values(metadata.get("persoon_op_afbeelding")):
            top.about = model.Person(label=person)
        portrait_person = _person_name_from_portrait_title(primary_title)
        if portrait_person:
            top.about = model.Person(label=portrait_person)

        for place in _values(metadata.get("adres")):
            top.about = model.Place(label=place)

        technique = _first(metadata, "techniek")
        if technique:
            activity = model.Activity(label=f"Technique: {technique}")
            activity.technique = model.Type(label=technique)
            top.used_for = activity

        production = model.Production()
        has_production = False
        for creator in _values(metadata.get("vervaardiger")):
            creator = _creator_name(creator)
            if creator:
                production.carried_out_by = model.Person(label=creator)
                has_production = True

        start_year, end_year = _year_range(_first(metadata, "datering") or _first(metadata, "datering_begin"))
        if start_year:
            timespan = model.TimeSpan()
            timespan.begin_of_the_begin = f"{start_year}-01-01T00:00:00"
            timespan.end_of_the_begin = f"{start_year}-12-31T23:59:59"
            if end_year:
                timespan.begin_of_the_end = f"{end_year}-01-01T00:00:00"
                timespan.end_of_the_end = f"{end_year}-12-31T23:59:59"
            production.timespan = timespan
            has_production = True

        for place in _values(metadata.get("land")):
            production.took_place_at = model.Place(label=place)
            has_production = True

        if has_production:
            top.produced_by = production

        top.current_owner = model.Group(label=self.owner_label)
        top.current_location = model.Place(label=self.owner_label)
        top.member_of = model.Set(label=self.collection_label)

        detail_url = _first(metadata, "pid") or rec.get("handle") or self.detail_base.format(record_id=record_id)
        page = model.LinguisticObject()
        webpage = vocab.WebPage(label="Object page at Noord-Hollands Archief")
        webpage.access_point = model.DigitalObject(ident=detail_url)
        webpage.format = "text/html"
        page.digitally_carried_by = webpage
        top.subject_of = page

        image_url = None
        for asset in rec.get("asset", []):
            image_url = (
                (asset.get("thumb") or {}).get("large")
                or asset.get("download")
                or (asset.get("thumb") or {}).get("medium")
            )
            if image_url:
                visual_item = model.VisualItem()
                digital = model.DigitalObject()
                digital.access_point = model.DigitalObject(ident=image_url)
                digital.format = "image/jpeg"
                visual_item.digitally_shown_by = digital
                top.representation = visual_item
                break

        data = model.factory.toJSON(top)
        if image_url:
            _append_iiif_manifest(data, _iiif_manifest_url(self.api_base, image_url, primary_title))
        return {"identifier": record_id, "data": data, "source": self.source_name}
