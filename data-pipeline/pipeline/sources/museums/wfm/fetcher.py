from pipeline.process.base.fetcher import Fetcher


API_KEY = "0f18ed8a-b243-11e6-94c8-9f49a90dcd1d"
API_URL = "https://webservices.memorix.nl/mediabank"
DEFAULT_SORT = "random{1777977336382} asc"


class WfmFetcher(Fetcher):
    """Fetch Westfries Museum records from the Memorix mediabank API."""

    def __init__(self, config):
        Fetcher.__init__(self, config)
        self.api_key = config.get("apiKey", API_KEY)
        self.api_url = config.get("apiUrl", API_URL).rstrip("/")
        self.timeout = 30
        self.session.headers.update({"Accept": "application/json"})

    def validate_identifier(self, identifier):
        return bool(str(identifier or "").strip())

    def make_fetch_uri(self, identifier):
        if not self.validate_identifier(identifier):
            return None
        return f"{self.api_url}/media/{identifier}"

    def _params(self, **extra):
        params = {"apiKey": self.api_key, "lang": "nl"}
        params.update({k: v for k, v in extra.items() if v is not None})
        return params

    def fetch_page(self, page=1, rows=100, sort=DEFAULT_SORT):
        response = self.session.get(
            f"{self.api_url}/media",
            params=self._params(page=page, rows=rows, sort=sort),
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def fetch_record_by_page(self, page):
        payload = self.fetch_page(page=page, rows=1)
        records = payload.get("media") or []
        return records[0] if records else None

    def fetch(self, identifier):
        if not self.enabled:
            print(f"Called fetch for {self.name}:{identifier} but network is disabled")
            return None
        if not self.validate_identifier(identifier):
            print(f"Invalid identifier for {self.name}: {identifier}")
            return None

        try:
            response = self.session.get(
                self.make_fetch_uri(identifier),
                params=self._params(),
                timeout=self.timeout,
            )
            response.raise_for_status()
        except Exception:
            print(f"Failed to get response from {self.make_fetch_uri(identifier)}")
            return None

        payload = response.json()
        records = payload.get("media") or []
        if not records:
            return None
        return {"data": records[0], "source": self.name, "identifier": str(identifier)}
