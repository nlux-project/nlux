from pipeline.sources.museums.nha.c587.fetcher import API_KEY, API_URL, NhaC587Fetcher


COLLECTION_FILTER = 'search_s_collectie:"480 - historieprenten van de Provinciale Atlas Noord-Holland, Collectie van"'


class NhaC480Fetcher(NhaC587Fetcher):
    """Fetch NHA C480 history print records from the Memorix mediabank API."""

    def __init__(self, config):
        cfg = dict(config)
        cfg.setdefault("collectionFilter", COLLECTION_FILTER)
        cfg.setdefault("apiKey", API_KEY)
        cfg.setdefault("apiUrl", API_URL)
        super().__init__(cfg)
