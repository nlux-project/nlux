import re
from urllib.parse import urljoin

from cromulent import model, vocab
from pipeline.process.base.mapper import Mapper


FHM_URI = "http://www.wikidata.org/entity/Q574961"
FHM_LABEL = "Frans Hals Museum"
FHM_COLLECTION_LABEL = "Frans Hals Museum collection"
FHM_BASE = "https://collectie.franshalsmuseum.nl/"


def _clean(value):
    if value is None:
        return None
    value = re.sub(r"\s+", " ", str(value)).strip()
    return value or None


def _clean_artist(value):
    value = _clean(value)
    if not value:
        return None
    return value.split(",", 1)[0].strip()


def _first_year(value):
    match = re.search(r"\b(\d{4})\b", value or "")
    return match.group(1) if match else None


def _last_year(value):
    years = re.findall(r"\b(\d{2,4})\b", value or "")
    if not years:
        return None
    first = _first_year(value)
    last = years[-1]
    if len(last) == 2 and first:
        last = first[:2] + last
    return last


def _dimension_from_text(value):
    match = re.search(r"([\d,.]+)\s*x\s*([\d,.]+)\s*([a-zA-Z]+)", value or "")
    if not match:
        return None
    dim = model.Dimension()
    dim.value = float(match.group(1).replace(",", "."))
    dim.unit = model.MeasurementUnit(label=match.group(3))
    return dim


class FhmMapper(Mapper):
    def __init__(self, config):
        Mapper.__init__(self, config)
        self.namespace = config["namespace"]

    def transform(self, record, rectype=None, reference=False):
        rec = record.get("data", {})
        if isinstance(rec, dict) and "data" in rec:
            rec = rec["data"]

        objectid = str(rec.get("objectid", ""))
        if not objectid:
            return None

        uri = f"{self.namespace}{objectid}"
        titles = [_clean(title) for title in rec.get("titles", []) if _clean(title)]
        primary_title = titles[0] if titles else _clean(rec.get("object_name"))

        top = model.HumanMadeObject(ident=uri, label=primary_title)

        object_name = _clean(rec.get("object_name"))
        if object_name:
            top.classified_as = model.Type(label=object_name)

        for index, title in enumerate(titles):
            if index == 0:
                top.identified_by = vocab.PrimaryName(content=title)
            else:
                top.identified_by = vocab.AlternateName(content=title)

        inventory_number = _clean(rec.get("inventory_number"))
        if inventory_number:
            top.identified_by = vocab.AccessionNumber(content=inventory_number)

        prod = model.Production()
        artist = _clean_artist(rec.get("artist"))
        if artist:
            prod.carried_out_by = model.Person(label=artist)

        dating = _clean(rec.get("dating"))
        if dating:
            timespan = model.TimeSpan()
            start = _first_year(dating)
            end = _last_year(dating)
            if start:
                timespan.begin_of_the_begin = f"{start}-01-01T00:00:00"
                timespan.end_of_the_begin = f"{start}-12-31T23:59:59"
            if end:
                timespan.begin_of_the_end = f"{end}-01-01T00:00:00"
                timespan.end_of_the_end = f"{end}-12-31T23:59:59"
            timespan.identified_by = vocab.DisplayName(content=dating)
            prod.timespan = timespan
        if artist or dating:
            top.produced_by = prod

        material = _clean(rec.get("material"))
        if material:
            top.made_of = model.Material(label=material)

        dim = _dimension_from_text(rec.get("dimensions"))
        if dim:
            top.dimension = dim

        for key in ("provenance", "reproduction", "copyright", "object_status", "other_numbers"):
            content = _clean(rec.get(key))
            if content:
                top.referred_to_by = model.LinguisticObject(content=content)

        top.current_owner = model.Group(ident=FHM_URI, label=FHM_LABEL)
        top.member_of = model.Set(label=FHM_COLLECTION_LABEL)

        deeplink = _clean(rec.get("deeplink")) or uri
        page = model.LinguisticObject()
        do = vocab.WebPage(label="Object page at Frans Hals Museum")
        do.access_point = model.DigitalObject(ident=deeplink)
        do.format = "text/html"
        page.digitally_carried_by = do
        top.subject_of = page

        image_dzi = _clean(rec.get("image_dzi"))
        if image_dzi:
            vis = model.VisualItem()
            dobj = model.DigitalObject()
            dobj.access_point = model.DigitalObject(ident=urljoin(FHM_BASE, image_dzi))
            dobj.format = "application/xml"
            vis.digitally_shown_by = dobj
            top.representation = vis

        data = model.factory.toJSON(top)
        return {"identifier": objectid, "data": data, "source": "fhm"}
