from pipeline.process.base.mapper import Mapper
from cromulent import model, vocab

IMAGE_BASE = (
    "https://teylers.adlibhosting.com/ais6/Content/GetContent"
    "?command=getcontent&server=images&value={filename}"
    "&folderId=1&width=800&height=800&imageformat=jpg"
)
DETAIL_BASE = "https://teylers.adlibhosting.com/ais6/Details/museum/{priref}"

# Teylers Museum as current_owner (Wikidata Q751582)
TEYLERS_URI = "http://www.wikidata.org/entity/Q751582"
TEYLERS_LABEL = "Teylers Museum"

# Dutch object_name → (cromulent class, AAT URI, AAT label)
_OBJECT_TYPE_MAP = {
    # Paintings & drawings
    "schilderij":            (model.HumanMadeObject, "http://vocab.getty.edu/aat/300033618", "paintings (visual works)"),
    "tekening":              (model.HumanMadeObject, "http://vocab.getty.edu/aat/300033973", "drawings (visual works)"),
    "prent":                 (model.HumanMadeObject, "http://vocab.getty.edu/aat/300041273", "prints (visual works)"),
    "grafiek":               (model.HumanMadeObject, "http://vocab.getty.edu/aat/300041273", "prints (visual works)"),
    "aquarel":               (model.HumanMadeObject, "http://vocab.getty.edu/aat/300078925", "watercolors (paintings)"),
    "penseel in waterverf":  (model.HumanMadeObject, "http://vocab.getty.edu/aat/300078925", "watercolors (paintings)"),
    "gouache":               (model.HumanMadeObject, "http://vocab.getty.edu/aat/300015017", "gouaches (paintings)"),
    "schetsboek":            (model.HumanMadeObject, "http://vocab.getty.edu/aat/300027354", "sketchbooks"),
    # Sculpture
    "sculptuur":             (model.HumanMadeObject, "http://vocab.getty.edu/aat/300047090", "sculpture (visual works)"),
    "beeld":                 (model.HumanMadeObject, "http://vocab.getty.edu/aat/300047090", "sculpture (visual works)"),
    # Natural history
    "fossiel":               (model.HumanMadeObject, "http://vocab.getty.edu/aat/300380921", "fossils"),
    "mineraal":              (model.HumanMadeObject, "http://vocab.getty.edu/aat/300011068", "minerals"),
    # Scientific instruments
    "instrument":            (model.HumanMadeObject, "http://vocab.getty.edu/aat/300266639", "scientific instruments"),
    # Coins & medals — map all Dutch coin denominations to aat:300037222
    "munt":                  (model.HumanMadeObject, "http://vocab.getty.edu/aat/300037222", "coins (money)"),
    "duit":                  (model.HumanMadeObject, "http://vocab.getty.edu/aat/300037222", "coins (money)"),
    "gulden":                (model.HumanMadeObject, "http://vocab.getty.edu/aat/300037222", "coins (money)"),
    "stuiver":               (model.HumanMadeObject, "http://vocab.getty.edu/aat/300037222", "coins (money)"),
    "dubbele stuiver":       (model.HumanMadeObject, "http://vocab.getty.edu/aat/300037222", "coins (money)"),
    "daalder":               (model.HumanMadeObject, "http://vocab.getty.edu/aat/300037222", "coins (money)"),
    "leeuwendaalder":        (model.HumanMadeObject, "http://vocab.getty.edu/aat/300037222", "coins (money)"),
    "gouden dukaat":         (model.HumanMadeObject, "http://vocab.getty.edu/aat/300037222", "coins (money)"),
    "zilveren dukaat":       (model.HumanMadeObject, "http://vocab.getty.edu/aat/300037222", "coins (money)"),
    "zilveren rijder":       (model.HumanMadeObject, "http://vocab.getty.edu/aat/300037222", "coins (money)"),
    "denarius":              (model.HumanMadeObject, "http://vocab.getty.edu/aat/300037222", "coins (money)"),
    "cent":                  (model.HumanMadeObject, "http://vocab.getty.edu/aat/300037222", "coins (money)"),
    "halve cent":            (model.HumanMadeObject, "http://vocab.getty.edu/aat/300037222", "coins (money)"),
    "antoninianus":          (model.HumanMadeObject, "http://vocab.getty.edu/aat/300037222", "coins (money)"),
    "groot":                 (model.HumanMadeObject, "http://vocab.getty.edu/aat/300037222", "coins (money)"),
    "follis":                (model.HumanMadeObject, "http://vocab.getty.edu/aat/300037222", "coins (money)"),
    "driegulden":            (model.HumanMadeObject, "http://vocab.getty.edu/aat/300037222", "coins (money)"),
    "scheepjesschelling":    (model.HumanMadeObject, "http://vocab.getty.edu/aat/300037222", "coins (money)"),
    "rijdergulden":          (model.HumanMadeObject, "http://vocab.getty.edu/aat/300037222", "coins (money)"),
    "oord":                  (model.HumanMadeObject, "http://vocab.getty.edu/aat/300037222", "coins (money)"),
    "halve leeuwendaalder":  (model.HumanMadeObject, "http://vocab.getty.edu/aat/300037222", "coins (money)"),
    "halve zilveren rijder": (model.HumanMadeObject, "http://vocab.getty.edu/aat/300037222", "coins (money)"),
    "vijf cent (stuiver)":          (model.HumanMadeObject, "http://vocab.getty.edu/aat/300037222", "coins (money)"),
    "tien cent (dubbeltje)":        (model.HumanMadeObject, "http://vocab.getty.edu/aat/300037222", "coins (money)"),
    "vijfentwintig cent (kwartje)": (model.HumanMadeObject, "http://vocab.getty.edu/aat/300037222", "coins (money)"),
    "penning":               (model.HumanMadeObject, "http://vocab.getty.edu/aat/300435429", "medals (coins)"),
    # Books & manuscripts
    "boek":                  (model.LinguisticObject, "http://vocab.getty.edu/aat/300028051", "books"),
    "manuscript":            (model.LinguisticObject, "http://vocab.getty.edu/aat/300028569", "manuscripts (documents)"),
}

# Dutch dimension type → AAT URI
_DIM_TYPE_MAP = {
    "hoogte":   "http://vocab.getty.edu/aat/300055644",  # height
    "breedte":  "http://vocab.getty.edu/aat/300055647",  # width
    "diepte":   "http://vocab.getty.edu/aat/300072633",  # depth
    "diameter": "http://vocab.getty.edu/aat/300055624",  # diameter
    "gewicht":  "http://vocab.getty.edu/aat/300056240",  # weight
}


def _span_text(field):
    """Extract plain text from an Adlib grouped-output field value."""
    if field is None:
        return None
    spans = field.get("spans", [])
    if spans:
        return spans[0].get("text", "").strip() or None
    return None


def _group_values(group_list, field_name):
    """Yield text values for a named field across a list of grouped field dicts."""
    for entry in (group_list or []):
        val = _span_text(entry.get(field_name))
        if val:
            yield val


class TeylersMapper(Mapper):

    def __init__(self, config):
        Mapper.__init__(self, config)
        self.namespace = config["namespace"]

    def guess_type(self, data):
        obj_names = data.get("Object_name", [])
        for name in _group_values(obj_names, "object_name"):
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
            return None

        uri = f"{self.namespace}{priref}"

        # --- Determine type and AAT classification ---
        obj_names = rec.get("Object_name", [])
        cls = model.HumanMadeObject
        aat_uri = None
        aat_label = None
        for name in _group_values(obj_names, "object_name"):
            entry = _OBJECT_TYPE_MAP.get(name.lower())
            if entry:
                cls, aat_uri, aat_label = entry
                break

        # --- Primary title for _label ---
        titles = list(_group_values(rec.get("Title", []), "title"))
        primary_title = titles[0] if titles else None

        top = cls(ident=uri, label=primary_title)

        # classified_as: object type
        if aat_uri:
            top.classified_as = model.Type(ident=aat_uri, label=aat_label)

        # --- Titles → identified_by ---
        for i, title_text in enumerate(titles):
            if i == 0:
                top.identified_by = vocab.PrimaryName(content=title_text)
            else:
                top.identified_by = vocab.AlternateName(content=title_text)

        # --- Accession number ---
        obj_num = _span_text(rec.get("object_number"))
        if obj_num:
            top.identified_by = vocab.AccessionNumber(content=obj_num)

        # --- Production event: creator + timespan + technique ---
        production_list = rec.get("Production", [])
        dating_list = rec.get("Dating", [])
        technique_list = rec.get("Technique", [])

        has_production = bool(production_list or dating_list or technique_list)
        if has_production:
            prod = model.Production()

            for entry in production_list:
                creator_text = _span_text(entry.get("creator"))
                if creator_text:
                    # "Surname, Firstname (birth-death)" → strip dates
                    name_part = creator_text.split("(")[0].strip().rstrip(",").strip()
                    person = model.Person(label=name_part)
                    prod.carried_out_by = person

            if dating_list:
                d = dating_list[0]
                start = _span_text(d.get("dating.date.start"))
                end = _span_text(d.get("dating.date.end"))
                start_prec = _span_text(d.get("dating.date.start.prec"))
                end_prec = _span_text(d.get("dating.date.end.prec"))

                if start or end:
                    ts = model.TimeSpan()
                    if start:
                        ts.begin_of_the_begin = f"{start}-01-01T00:00:00"
                        ts.end_of_the_begin = f"{start}-12-31T23:59:59"
                    if end:
                        ts.begin_of_the_end = f"{end}-01-01T00:00:00"
                        ts.end_of_the_end = f"{end}-12-31T23:59:59"
                    label_parts = []
                    if start_prec:
                        label_parts.append(start_prec)
                    if start:
                        label_parts.append(start)
                    if end and end != start:
                        label_parts.append("-")
                        if end_prec:
                            label_parts.append(end_prec)
                        label_parts.append(end)
                    ts.identified_by = vocab.DisplayName(content=" ".join(label_parts))
                    prod.timespan = ts

            for tech_text in _group_values(technique_list, "technique"):
                prod.technique = model.Type(label=tech_text)
                break  # one technique per production event

            top.produced_by = prod

        # --- Material ---
        for mat_text in _group_values(rec.get("Material", []), "material"):
            top.made_of = model.Material(label=mat_text)

        # --- Dimensions ---
        for dim_entry in (rec.get("Dimension", []) or []):
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

        # --- Description → referred_to_by ---
        for desc_text in _group_values(rec.get("Description", []), "description"):
            top.referred_to_by = vocab.Description(content=desc_text)

        # --- Inscription ---
        for insc_text in _group_values(rec.get("Inscription", []), "inscription.content"):
            top.referred_to_by = model.LinguisticObject(content=insc_text)

        # --- Current owner: Teylers Museum ---
        top.current_owner = model.Group(ident=TEYLERS_URI, label=TEYLERS_LABEL)

        # --- Digital reference: detail page ---
        detail_url = DETAIL_BASE.format(priref=priref)
        page = model.LinguisticObject()
        do = vocab.WebPage(label="Object page at Teylers Museum")
        do.access_point = model.DigitalObject(ident=detail_url)
        do.format = "text/html"
        page.digitally_carried_by = do
        top.subject_of = page

        # --- Representation: first public image ---
        for media_entry in (rec.get("Media", []) or []):
            ref = media_entry.get("media.reference", {})
            publish = _span_text(ref.get("publish_on_web"))
            filename = _span_text(ref.get("reference_number"))
            if publish and filename:
                img_url = IMAGE_BASE.format(filename=filename)
                vis = model.VisualItem()
                dobj = model.DigitalObject(ident=img_url)
                dobj.format = "image/jpeg"
                vis.digitally_shown_by = dobj
                top.representation = vis
                break  # one representative image

        data = model.factory.toJSON(top)
        return {"identifier": priref, "data": data, "source": "teylers"}
