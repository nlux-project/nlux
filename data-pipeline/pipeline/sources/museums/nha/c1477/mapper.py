from pipeline.sources.museums.nha.mapper import NHA_DETAIL_BASE, NHA_LABEL, NhaMapper


NHA_COLLECTION_LABEL = "1477 - prenten van C.G. Voorhelm Schneevoogt te Haarlem"


class NhaC1477Mapper(NhaMapper):
    source_name = "nha-c1477"
    owner_label = NHA_LABEL
    collection_label = NHA_COLLECTION_LABEL
    detail_base = NHA_DETAIL_BASE
