from pipeline.sources.museums.nha.mapper import NHA_DETAIL_BASE, NHA_LABEL, NhaMapper


NHA_COLLECTION_LABEL = "359 - prenten en tekeningen van de Provinciale Atlas Noord-Holland"


class NhaC359Mapper(NhaMapper):
    source_name = "nha-c359"
    owner_label = NHA_LABEL
    collection_label = NHA_COLLECTION_LABEL
    detail_base = NHA_DETAIL_BASE
