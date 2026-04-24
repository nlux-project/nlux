import datetime

from pipeline.process.base.harvester import Harvester
from pipeline.sources.museums.hvh.parser import parse_list_identifiers_xml


class HvhHarvester(Harvester):
    """Harvest Huis van Hilde OAI-PMH identifiers and fetch full records."""

    def __init__(self, config):
        Harvester.__init__(self, config)
        self.endpoint = config["pmhEndpoint"]
        self.metadata_prefix = config.get("pmhMetadataPrefix", "oai_pnh")

    def make_pmh_uri(self, verb, token=None):
        if token:
            return f"{self.endpoint}?verb={verb}&resumptionToken={token}"
        return f"{self.endpoint}?verb={verb}&metadataPrefix={self.metadata_prefix}"

    def fetch_identifiers_page(self, uri):
        resp = self.session.get(uri, timeout=30)
        resp.raise_for_status()
        return parse_list_identifiers_xml(resp.text)

    def crawl(self, last_harvest=None):
        Harvester.crawl(self, last_harvest)
        next_uri = self.make_pmh_uri("ListIdentifiers")
        change_time = datetime.datetime.utcnow().isoformat()

        while next_uri:
            identifiers, token = self.fetch_identifiers_page(next_uri)
            for identifier in identifiers:
                record = self.fetcher.fetch(identifier)
                if record is not None:
                    yield ("update", identifier, record, change_time)
            next_uri = self.make_pmh_uri("ListIdentifiers", token) if token else None
