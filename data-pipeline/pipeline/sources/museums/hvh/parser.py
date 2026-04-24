from lxml import etree


OAI_NS = "http://www.openarchives.org/OAI/2.0/"
NS_PREFIXES = {
    "http://purl.org/dc/elements/1.1/": "dc",
    "http://purl.org/dc/terms/": "dcterms",
    "http://www.europeana.eu/schemas/edm/": "edm",
}


def _field_name(node):
    qname = etree.QName(node)
    prefix = NS_PREFIXES.get(qname.namespace)
    if prefix:
        return f"{prefix}:{qname.localname}"
    return qname.localname


def _field_value(node):
    value = (node.text or "").strip()
    return {
        "value": value,
        "attrs": {k: v for k, v in node.attrib.items()},
    }


def texts(data, key):
    values = data.get(key, [])
    output = []
    for value in values:
        if isinstance(value, dict):
            text = value.get("value", "")
        else:
            text = str(value)
        text = text.strip()
        if text:
            output.append(text)
    return output


def first_text(data, *keys):
    for key in keys:
        values = texts(data, key)
        if values:
            return values[0]
    return None


def first_value(data, *keys):
    for key in keys:
        values = data.get(key, [])
        if values:
            return values[0]
    return None


def parse_oai_record_xml(xml_text):
    dom = etree.fromstring(xml_text.encode("utf-8"))
    metadata = dom.find(f".//{{{OAI_NS}}}metadata")
    if metadata is None:
        return None

    record = {}
    for child in metadata:
        name = _field_name(child)
        record.setdefault(name, []).append(_field_value(child))

    header_identifier = dom.findtext(f".//{{{OAI_NS}}}header/{{{OAI_NS}}}identifier")
    if header_identifier:
        record.setdefault("oai:identifier", []).append({"value": header_identifier.strip(), "attrs": {}})

    header_dc_identifier = dom.findtext(f".//{{{OAI_NS}}}header/dc_identifier")
    if header_dc_identifier:
        record.setdefault("header:dc_identifier", []).append({"value": header_dc_identifier.strip(), "attrs": {}})

    return record


def parse_list_identifiers_xml(xml_text):
    dom = etree.fromstring(xml_text.encode("utf-8"))
    headers = dom.findall(f".//{{{OAI_NS}}}ListIdentifiers/{{{OAI_NS}}}header")
    identifiers = []
    for header in headers:
        ident = header.xpath("string(./*[local-name()='dc_identifier'][1])")
        if not ident:
            ident = header.findtext(f"{{{OAI_NS}}}identifier")
        if ident:
            identifiers.append(ident.strip())

    token = dom.findtext(f".//{{{OAI_NS}}}ListIdentifiers/{{{OAI_NS}}}resumptionToken")
    return identifiers, (token.strip() if token and token.strip() else None)
