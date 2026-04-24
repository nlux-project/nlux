from typing import Optional

from cromulent import model, vocab
from pipeline.process.base.mapper import Mapper


# CHT concepts that match known AAT material hierarchy roots are mapped to
# Material; everything else becomes Type.  The mapper does a simple
# heuristic based on the Dutch prefLabel; a more robust approach would
# inspect the broader hierarchy (not worth fetching individually online).
_MATERIAL_KEYWORDS = {
    "metaal", "hout", "papier", "textiel", "steen", "glas", "leer",
    "keramiek", "ivoor", "been", "was", "lak", "verf", "inkt", "pigment",
    "olie", "gouache", "aquarel", "pastel", "email", "zilver", "goud",
    "koper", "brons", "tin", "lood", "ijzer", "staal", "platina",
}


class ChtMapper(Mapper):
    """Map CHT SKOS-in-JSON records to Linked Art Type/Material stubs."""

    def guess_type(self, data: dict):
        label = data.get("_label", data.get("prefLabel", "")).lower()
        for kw in _MATERIAL_KEYWORDS:
            if kw in label:
                return model.Material
        return model.Type

    def transform(self, record: dict, rectype, reference=False) -> Optional[dict]:
        rec = record["data"]
        uri = rec.get("id", "")
        if not uri:
            return None

        if rectype is None or rectype == "Type":
            topcls = self.guess_type(rec)
        else:
            topcls = getattr(model, rectype, model.Type)

        pref_label = rec.get("_label", rec.get("prefLabel", ""))
        top = topcls(ident=uri, label=pref_label)

        # Primary Dutch name
        nl_lang = None
        try:
            ns = self.configs.external["aat"]["namespace"]
            gbls = self.configs.globals_cfg
            nl_lang = model.Language(
                ident=f"{ns}{gbls['lang_nl']}", label="Dutch"
            )
        except Exception:
            pass

        pn = vocab.PrimaryName(content=pref_label)
        if nl_lang:
            pn.language = nl_lang
        top.identified_by = pn

        # Alternate Dutch labels
        for alt in rec.get("altLabel", []):
            an = vocab.AlternateName(content=alt)
            if nl_lang:
                an.language = nl_lang
            top.identified_by = an

        # broader hierarchy (stub references only)
        for br in rec.get("broader", []):
            br_uri = br.get("id", "")
            if br_uri:
                top.broader = topcls(ident=br_uri)

        # Preserve skos:exactMatch to AAT (carried as equivalent in harvest file)
        for eq in rec.get("equivalent", []):
            eq_uri = eq.get("id", "")
            if eq_uri:
                top.equivalent = topcls(ident=eq_uri)

        data = model.factory.toJSON(top)
        return {"identifier": record["identifier"], "data": data, "source": "cht"}
