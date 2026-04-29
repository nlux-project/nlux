import re

from cromulent import model, vocab

from pipeline.process.base.mapper import Mapper
from pipeline.sources.museums.hvh.parser import first_text, first_value, texts


OWNER_URI = "https://collectie.huisvanhilde.nl/resource/organization/provinciaal-depot-voor-archeologie-noord-holland"
OWNER_LABEL = "Provinciaal Depot voor Archeologie Noord-Holland"
HVH_COLLECTION_LABEL = "Huis van Hilde"
YEAR_RANGE_RE = re.compile(r"^\s*(\d{1,4})\s*-\s*(\d{1,4})\s*$")
SINGLE_YEAR_RE = re.compile(r"^\s*(\d{1,4})\s*$")


def _year_start(year):
    return f"{int(year):04d}-01-01T00:00:00"


def _year_end(year):
    return f"{int(year):04d}-12-31T23:59:59"


def _set_timespan(prod, label):
    if not label:
        return

    match = YEAR_RANGE_RE.match(label)
    if match:
        begin, end = match.groups()
    else:
        match = SINGLE_YEAR_RE.match(label)
        if not match:
            return
        begin = end = match.group(1)

    ts = model.TimeSpan()
    ts.begin_of_the_begin = _year_start(begin)
    ts.end_of_the_end = _year_end(end)
    ts.identified_by = vocab.DisplayName(content=label)
    prod.timespan = ts


def _dedupe(values):
    seen = set()
    output = []
    for value in values:
        if value not in seen:
            seen.add(value)
            output.append(value)
    return output


def _attrs(data, key):
    value = first_value(data, key)
    if isinstance(value, dict):
        return value.get("attrs", {}) or {}
    return {}


def _values(data, key):
    for value in data.get(key, []) or []:
        if isinstance(value, dict):
            text = value.get("value", "").strip()
            attrs = value.get("attrs", {}) or {}
        else:
            text = str(value).strip()
            attrs = {}
        if text:
            yield text, attrs


def _join_place_name(name, attrs):
    parts = [name]
    for key in ("plaats", "gemeente", "regio"):
        value = attrs.get(key)
        if value and value not in parts:
            parts.append(value)
    return ", ".join(parts)


class HvhMapper(Mapper):
    def __init__(self, config):
        Mapper.__init__(self, config)
        self.namespace = config["namespace"]

    def guess_type(self, data):
        return model.HumanMadeObject

    def transform(self, record, rectype=None, reference=False):
        rec = record.get("data", {})
        if isinstance(rec, dict) and "data" in rec:
            rec = rec["data"]

        identifier = first_text(rec, "dc:identifier", "header:dc_identifier")
        if not identifier:
            return None

        uri = f"{self.namespace}{identifier}"
        primary_title = first_text(rec, "dc:title", "title", "dc:subject") or identifier
        top = model.HumanMadeObject(ident=uri, label=primary_title)

        top.identified_by = vocab.PrimaryName(content=primary_title)
        top.identified_by = vocab.AccessionNumber(content=identifier)

        for alt_title in texts(rec, "title"):
            if alt_title != primary_title:
                top.identified_by = vocab.AlternateName(content=alt_title)

        for desc in texts(rec, "dc:description"):
            top.referred_to_by = vocab.Description(content=desc)

        for statement in texts(rec, "dc_format"):
            top.referred_to_by = vocab.DimensionStatement(content=statement)

        for material in texts(rec, "dcterms_medium"):
            top.made_of = model.Material(label=material)

        temporal = first_text(rec, "dcterms:temporal")
        production = None
        if temporal:
            production = model.Production()
            _set_timespan(production, temporal)
            if hasattr(production, "timespan"):
                top.produced_by = production

        creators = list(_values(rec, "dc_creator"))
        for creator, attrs in creators:
            role_label = attrs.get("Role")
            if role_label:
                top.referred_to_by = vocab.Note(content=f"{role_label}: {creator}")

        classifications = []
        for field in ("objecttype", "dc:subject", "thesvondst", "dcterms:temporalperiod", "periodezoeken", "thesperiode", "rubriek"):
            classifications.extend(texts(rec, field))
        for label in _dedupe(classifications):
            top.classified_as = model.Type(label=label)

        top.current_owner = model.Group(ident=OWNER_URI, label=OWNER_LABEL)
        top.member_of = model.Set(label=HVH_COLLECTION_LABEL)

        storage = first_text(rec, "Standplaats")
        if storage:
            top.current_location = model.Place(label=storage)

        findspot = first_text(rec, "vindplaats")
        if findspot:
            attrs = _attrs(rec, "vindplaats")
            encounter = model.Encounter()
            encounter.took_place_at = model.Place(label=_join_place_name(findspot, attrs))
            if attrs.get("onderzoek"):
                encounter.classified_as = model.Type(label=attrs["onderzoek"])
            if attrs.get("jaar"):
                _set_timespan(encounter, attrs["jaar"])
            for creator, creator_attrs in creators:
                group = model.Group(label=creator)
                if creator_attrs.get("creatorandrole"):
                    group.identified_by = vocab.DisplayName(content=creator_attrs["creatorandrole"])
                encounter.carried_out_by = group
            top.encountered_by = encounter

        rel_site = first_value(rec, "relobjectsites")
        if isinstance(rel_site, dict):
            site_attrs = rel_site.get("attrs", {}) or {}
            site_name = site_attrs.get("sitename")
            site_url = site_attrs.get("deeplinksitepubl")
            if site_name:
                top.referred_to_by = vocab.Note(content=f"Vindplaats: {site_name}")
            if site_url:
                page = model.LinguisticObject(label=f"Site page at Huis van Hilde: {site_name or rel_site.get('value')}")
                webpage = vocab.WebPage(label="Findspot page at Huis van Hilde")
                webpage.access_point = model.DigitalObject(ident=site_url)
                webpage.format = "text/html"
                page.digitally_carried_by = webpage
                top.subject_of = page

        page_url = first_text(rec, "deeplinkpubl")
        if page_url:
            page = model.LinguisticObject()
            webpage = vocab.WebPage(label="Object page at Huis van Hilde")
            webpage.access_point = model.DigitalObject(ident=page_url)
            webpage.format = "text/html"
            page.digitally_carried_by = webpage
            top.subject_of = page

        image_url = first_text(rec, "europeana_isshownby")
        if image_url:
            visual = model.VisualItem()
            digital = model.DigitalObject(ident=image_url)
            digital.format = "image/jpeg"
            visual.digitally_shown_by = digital
            top.representation = visual

        data = model.factory.toJSON(top)
        return {"identifier": identifier, "data": data, "source": "hvh"}
