import re

from cromulent import model, vocab

from pipeline.process.base.mapper import Mapper
from pipeline.sources.museums.hvh.parser import first_text, texts


OWNER_URI = "https://collectie.huisvanhilde.nl/resource/organization/provinciaal-depot-voor-archeologie-noord-holland"
OWNER_LABEL = "Provinciaal Depot voor Archeologie Noord-Holland"
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

        for material in texts(rec, "dcterms_medium"):
            top.made_of = model.Material(label=material)

        temporal = first_text(rec, "dcterms:temporal")
        if temporal:
            production = model.Production()
            _set_timespan(production, temporal)
            if hasattr(production, "timespan"):
                top.produced_by = production

        for field in ("objecttype", "dc:subject", "thesvondst", "dcterms:temporalperiod", "rubriek"):
            for label in texts(rec, field):
                top.classified_as = model.Type(label=label)

        top.current_owner = model.Group(ident=OWNER_URI, label=OWNER_LABEL)

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
