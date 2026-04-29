from pipeline.process.base.fetcher import Fetcher


WEBAPI = "https://mmb-web.adlibhosting.com/ais6/webapi/wwwopac.ashx"
FIELDS = (
    "priref,object_number,title,object_name,"
    "creator,creator.role,"
    "production.date.start,production.date.end,"
    "description,inscription.content,"
    "dimension,dimension.type,dimension.value,dimension.unit,"
    "material,technique,"
    "association.person,association.subject,"
    "location.default.name,"
    "reproduction.reference"
)


class RbhcFetcher(Fetcher):
    """Fetch a single Rijksmuseum Boerhaave collection record by priref."""

    def __init__(self, config):
        Fetcher.__init__(self, config)
        self.webapi = WEBAPI

    def validate_identifier(self, identifier):
        return str(identifier).isdigit()

    def make_fetch_uri(self, identifier):
        return (
            f"{self.webapi}?database=collect"
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
