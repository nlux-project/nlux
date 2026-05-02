import ujson as json

from pipeline.process.base.fetcher import Fetcher
from pipeline.sources.museums.fhm.parser import parse_search_response


SEARCH_ENDPOINT = "https://collectie.franshalsmuseum.nl/cc/ccConnector.asmx/search"


class FhmFetcher(Fetcher):
    """Fetch a single Frans Hals Museum record from CollectionConnection."""

    def __init__(self, config):
        Fetcher.__init__(self, config)
        self.endpoint = SEARCH_ENDPOINT
        self.timeout = 30
        self.session.headers.update({"Content-Type": "application/json; charset=utf-8"})

    def validate_identifier(self, identifier):
        return str(identifier).isdigit()

    def make_fetch_uri(self, identifier):
        if not self.validate_identifier(identifier):
            return None
        return self.endpoint

    def make_search_spec(self, identifier=None, first=1):
        search_value = "*" if identifier is None else str(identifier)
        search_tag = "Alle velden" if identifier is None else "objectid"
        return {
            "ccSettingsName": "Alternative",
            "numPerPage": 1,
            "oldNumPerPage": 12,
            "sortfield": "Relevantie",
            "filter": {},
            "facetValues": {},
            "facetSort": {},
            "basketFilters": [],
            "queryFilters": [],
            "showtype": "record",
            "oldShowtype": "list",
            "first": first,
            "filename": "",
            "articlename": "",
            "searchValues": [{"id": 0, "tag": search_tag, "value": search_value}],
        }

    def fetch_search(self, identifier=None, first=1):
        payload = {
            "searchSpecStr": json.dumps(self.make_search_spec(identifier=identifier, first=first)),
            "authToken": "",
        }
        response = self.session.post(self.endpoint, data=json.dumps(payload), timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def fetch_record_by_offset(self, first):
        payload = self.fetch_search(first=first)
        return parse_search_response(payload)

    def fetch(self, identifier):
        if not self.enabled:
            print(f"Called fetch for {self.name}:{identifier} but network is disabled")
            return None
        if not self.validate_identifier(identifier):
            print(f"Invalid identifier for {self.name}: {identifier}")
            return None

        try:
            payload = self.fetch_search(identifier=identifier)
        except Exception:
            print(f"Failed to get response from {self.endpoint}")
            return None

        data = parse_search_response(payload)
        if not data:
            return None
        return {"data": data, "source": self.name, "identifier": str(identifier)}
