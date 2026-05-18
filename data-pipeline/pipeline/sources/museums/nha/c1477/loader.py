from pipeline.sources.museums.nha.c587.loader import NhaC587Loader


class NhaC1477Loader(NhaC587Loader):
    """Load NHA C1477 records from harvested Memorix JSON files."""

    source_label = "NHA C1477"
    collection_dir = "c1477"
