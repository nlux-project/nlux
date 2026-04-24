import re

from pipeline.process.base.fetcher import Fetcher
from pipeline.sources.museums.hvh.parser import parse_oai_record_xml


OAI_ENDPOINT = "http://62.221.199.184:17518/oai"
IDENTIFIER_RE = re.compile(r"^[0-9A-Za-z][0-9A-Za-z._-]*$")


class HvhFetcher(Fetcher):
    """Fetch a single Huis van Hilde record by OAI identifier."""

    def __init__(self, config):
        Fetcher.__init__(self, config)
        self.oai_endpoint = config.get("pmhEndpoint", OAI_ENDPOINT)

    def validate_identifier(self, identifier):
        return bool(IDENTIFIER_RE.match(identifier))

    def make_fetch_uri(self, identifier):
        if not self.validate_identifier(identifier):
            return None
        return (
            f"{self.oai_endpoint}?verb=GetRecord"
            f"&metadataPrefix=oai_pnh"
            f"&identifier={identifier}"
        )

    def post_process(self, data, identifier):
        xml_text = data.get("value", "")
        if not xml_text:
            return None
        return parse_oai_record_xml(xml_text)
