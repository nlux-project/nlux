from pipeline.sources.museums.nha.c587.fetcher import API_KEY, API_URL, NhaC587Fetcher


COLLECTION_FILTER = 'search_s_collectie:"1477 - prenten van C.G. Voorhelm Schneevoogt te Haarlem, Collectie van"'


class NhaC1477Fetcher(NhaC587Fetcher):
    """Fetch NHA C1477 print records from the Memorix mediabank API."""

    def __init__(self, config):
        cfg = dict(config)
        cfg.setdefault("collectionFilter", COLLECTION_FILTER)
        cfg.setdefault("apiKey", API_KEY)
        cfg.setdefault("apiUrl", API_URL)
        super().__init__(cfg)
