import ujson as json
import requests
from pipeline.process.base.fetcher import Fetcher

WEBAPI = "https://teylers.adlibhosting.com/ais6/webapi/wwwopac.ashx"
FIELDS = (
    "priref,object_number,title,title.type,"
    "creator,creator.role,"
    "dating.date.start,dating.date.start.prec,"
    "dating.date.end,dating.date.end.prec,"
    "object_name,material,technique,"
    "dimension,dimension.type,dimension.value,dimension.unit,"
    "content.subject,content.place,"
    "media.reference"
)


class TeylersFetcher(Fetcher):
    """Fetch a single Teylers record by priref from the Adlib webapi."""

    def __init__(self, config):
        Fetcher.__init__(self, config)
        self.webapi = WEBAPI

    def validate_identifier(self, identifier):
        return identifier.isdigit()

    def make_fetch_uri(self, identifier):
        return (
            f"{self.webapi}?database=museum"
            f"&search=priref+%3D+{identifier}"
            f"&output=json&limit=1"
            f"&fields={FIELDS}"
        )

    def post_process(self, data, identifier):
        try:
            records = data["adlibJSON"]["recordList"]["record"]
            if records:
                return records[0]
        except (KeyError, IndexError, TypeError):
            pass
        return None
