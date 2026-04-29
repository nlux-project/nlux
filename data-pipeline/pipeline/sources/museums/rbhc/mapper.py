from pipeline.process.base.mapper import Mapper
from cromulent import model, vocab


IMAGE_BASE = (
    "https://mmb-web.adlibhosting.com/ais6/webapi/wwwopac.ashx"
    "?command=getcontent&server=images&value={filename}"
    "&folderId=2&width=800&height=800&imageformat=jpg"
)
DETAIL_BASE = "https://mmb-web.adlibhosting.com/ais6/Details/collect/{priref}"

RBHC_URI = "http://www.wikidata.org/entity/Q759169"
RBHC_LABEL = "Rijksmuseum Boerhaave"
RBHC_COLLECTION_LABEL = "Rijksmuseum Boerhaave collection"

_OBJECT_TYPE_MAP = {
    "instrument": (model.HumanMadeObject, "http://vocab.getty.edu/aat/300266639", "scientific instruments"),
    "microscoop": (model.HumanMadeObject, "http://vocab.getty.edu/aat/300024759", "microscopes"),
    "telescoop": (model.HumanMadeObject, "http://vocab.getty.edu/aat/300033201", "telescopes"),
    "prent": (model.HumanMadeObject, "http://vocab.getty.edu/aat/300041273", "prints (visual works)"),
    "boek": (model.LinguisticObject, "http://vocab.getty.edu/aat/300028051", "books"),
}

_DIM_TYPE_MAP = {
    "hoogte": "http://vocab.getty.edu/aat/300055644",
    "breedte": "http://vocab.getty.edu/aat/300055647",
    "diepte": "http://vocab.getty.edu/aat/300072633",
    "diameter": "http://vocab.getty.edu/aat/300055624",
    "gewicht": "http://vocab.getty.edu/aat/300056240",
}


def _span_text(field):
    """Extract text from Adlib grouped values, preferring Dutch when present."""
    if field is None:
        return None
    if isinstance(field, str):
        return field.strip() or None
    if isinstance(field, list):
        for lang in ("nl-NL", "en-GB"):
            for item in field:
                if item.get("lang") == lang:
                    val = _span_text(item.get("value", item))
                    if val:
                        return val
        for item in field:
            val = _span_text(item.get("value", item))
            if val:
                return val
        return None
    if isinstance(field, dict):
        if "value" in field:
            return _span_text(field.get("value"))
        spans = field.get("spans", [])
        if spans:
            return spans[0].get("text", "").strip() or None
    return None


def _group_values(group_list, field_name):
    for entry in group_list or []:
        val = _span_text(entry.get(field_name))
        if val:
            yield val


def _clean_creator_name(value):
    # Boerhaave often stores "Name; Place"; keep the name as the agent label.
    return value.split(";")[0].strip().rstrip(",").strip()


class RbhcMapper(Mapper):
    def __init__(self, config):
        Mapper.__init__(self, config)
        self.namespace = config["namespace"]

    def guess_type(self, data):
        for name in _group_values(data.get("Object_name", []), "object_name"):
            entry = _OBJECT_TYPE_MAP.get(name.lower())
            if entry:
                return entry[0]
        return model.HumanMadeObject

    def transform(self, record, rectype=None, reference=False):
        rec = record.get("data", {})
        if isinstance(rec, dict) and "data" in rec:
            rec = rec["data"]

        priref = str(rec.get("@priref", ""))
        if not priref:
            priref = _span_text(rec.get("priref")) or ""
        if not priref:
            return None

        uri = f"{self.namespace}{priref}"
        object_names = list(_group_values(rec.get("Object_name", []), "object_name"))
        titles = list(_group_values(rec.get("Title", []), "title"))
        primary_title = titles[0] if titles else (object_names[0] if object_names else None)

        cls = model.HumanMadeObject
        aat_uri = None
        aat_label = None
        object_type_label = object_names[0] if object_names else None
        for name in object_names:
            entry = _OBJECT_TYPE_MAP.get(name.lower())
            if entry:
                cls, aat_uri, aat_label = entry
                break

        top = cls(ident=uri, label=primary_title)

        if aat_uri:
            top.classified_as = model.Type(ident=aat_uri, label=aat_label)
        elif object_type_label:
            top.classified_as = model.Type(label=object_type_label)

        for i, title_text in enumerate(titles):
            if i == 0:
                top.identified_by = vocab.PrimaryName(content=title_text)
            else:
                top.identified_by = vocab.AlternateName(content=title_text)

        obj_num = _span_text(rec.get("object_number"))
        if obj_num:
            top.identified_by = vocab.AccessionNumber(content=obj_num)

        production_list = rec.get("Production", [])
        dating_list = rec.get("Production_date", [])
        technique_list = rec.get("Technique", [])
        if production_list or dating_list or technique_list:
            prod = model.Production()

            for entry in production_list:
                creator_text = _span_text(entry.get("creator"))
                if creator_text:
                    prod.carried_out_by = model.Person(label=_clean_creator_name(creator_text))

            if dating_list:
                d = dating_list[0]
                start = _span_text(d.get("production.date.start"))
                end = _span_text(d.get("production.date.end"))
                if start or end:
                    ts = model.TimeSpan()
                    if start:
                        ts.begin_of_the_begin = f"{start}-01-01T00:00:00"
                        ts.end_of_the_begin = f"{start}-12-31T23:59:59"
                    if end:
                        ts.begin_of_the_end = f"{end}-01-01T00:00:00"
                        ts.end_of_the_end = f"{end}-12-31T23:59:59"
                    ts.identified_by = vocab.DisplayName(content=" - ".join([x for x in (start, end) if x]))
                    prod.timespan = ts

            for tech_text in _group_values(technique_list, "technique"):
                prod.technique = model.Type(label=tech_text)
                break

            top.produced_by = prod

        for mat_text in _group_values(rec.get("Material", []), "material"):
            top.made_of = model.Material(label=mat_text)

        for dim_entry in rec.get("Dimension", []) or []:
            val = _span_text(dim_entry.get("dimension.value"))
            unit_text = _span_text(dim_entry.get("dimension.unit"))
            dim_type = _span_text(dim_entry.get("dimension.type"))
            if val and unit_text:
                meas = model.Dimension()
                try:
                    meas.value = float(val.replace(",", "."))
                except ValueError:
                    continue
                meas.unit = model.MeasurementUnit(label=unit_text)
                if dim_type:
                    aat = _DIM_TYPE_MAP.get(dim_type.lower())
                    if aat:
                        meas.classified_as = model.Type(ident=aat, label=dim_type)
                top.dimension = meas

        for desc_text in _group_values(rec.get("Description", []), "description"):
            top.referred_to_by = vocab.Description(content=desc_text)

        for insc_text in _group_values(rec.get("Inscription", []), "inscription.content"):
            top.referred_to_by = model.LinguisticObject(content=insc_text)

        location = _span_text(rec.get("location.default.name"))
        if location:
            top.current_location = model.Place(label=location)

        for subject_text in _group_values(rec.get("Associated_subject", []), "association.subject"):
            top.about = model.Type(label=subject_text)

        top.current_owner = model.Group(ident=RBHC_URI, label=RBHC_LABEL)
        top.member_of = model.Set(label=RBHC_COLLECTION_LABEL)

        detail_url = DETAIL_BASE.format(priref=priref)
        page = model.LinguisticObject()
        do = vocab.WebPage(label="Object page at Rijksmuseum Boerhaave")
        do.access_point = model.DigitalObject(ident=detail_url)
        do.format = "text/html"
        page.digitally_carried_by = do
        top.subject_of = page

        for repro_entry in rec.get("Reproduction", []) or []:
            filename = _span_text(repro_entry.get("reproduction.reference"))
            if filename:
                vis = model.VisualItem()
                dobj = model.DigitalObject(ident=IMAGE_BASE.format(filename=filename))
                dobj.format = "image/jpeg"
                vis.digitally_shown_by = dobj
                top.representation = vis
                break

        data = model.factory.toJSON(top)
        return {"identifier": priref, "data": data, "source": "rbhc"}
