from pipeline.sources.museums.nha.c587.mapper import NHA_DETAIL_BASE, NHA_LABEL, NhaC587Mapper


NHA_COLLECTION_LABEL = "480 - historieprenten van de Provinciale Atlas Noord-Holland, Collectie van"


class NhaC480Mapper(NhaC587Mapper):
    source_name = "nha-c480"
    owner_label = NHA_LABEL
    collection_label = NHA_COLLECTION_LABEL
    detail_base = NHA_DETAIL_BASE

