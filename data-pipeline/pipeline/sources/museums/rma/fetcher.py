from urllib.parse import urlparse

from pipeline.process.base.fetcher import Fetcher


SEARCH_URL = "https://data.rijksmuseum.nl/search/collection"
RESOLVER_BASE = "https://id.rijksmuseum.nl"


class RmaFetcher(Fetcher):
    """Fetch Rijksmuseum Amsterdam Linked Art records."""

    def __init__(self, config):
        Fetcher.__init__(self, config)
        self.search_url = config.get("searchUrl", SEARCH_URL)
        self.resolver_base = config.get("resolverBase", RESOLVER_BASE).rstrip("/")
        self.timeout = 30
        self.session.headers.update({"Accept": "application/ld+json, application/json"})

    def fix_identifier(self, identifier):
        identifier = str(identifier or "").strip()
        if identifier.startswith("http://") or identifier.startswith("https://"):
            path = urlparse(identifier).path.strip("/")
            return path.rsplit("/", 1)[-1]
        return identifier.strip("/")

    def validate_identifier(self, identifier):
        return bool(self.fix_identifier(identifier))

    def make_fetch_uri(self, identifier):
        identifier = self.fix_identifier(identifier)
        if not identifier:
            return None
        return f"{self.resolver_base}/{identifier}"

    def fetch_search_page(self, url=None, **params):
        response = self.session.get(url or self.search_url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def fetch(self, identifier):
        if not self.enabled:
            print(f"Called fetch for {self.name}:{identifier} but network is disabled")
            return None
        if not self.validate_identifier(identifier):
            print(f"Invalid identifier for {self.name}: {identifier}")
            return None

        identifier = self.fix_identifier(identifier)
        try:
            response = self.session.get(
                self.make_fetch_uri(identifier),
                params={"_profile": "la", "_mediatype": "application/ld+json"},
                timeout=self.timeout,
            )
            response.raise_for_status()
        except Exception:
            print(f"Failed to get response from {self.make_fetch_uri(identifier)}")
            return None

        return {"data": response.json(), "source": self.name, "identifier": identifier}
