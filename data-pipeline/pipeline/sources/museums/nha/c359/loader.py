from pipeline.sources.museums.nha.c587.loader import NhaC587Loader


class NhaC359Loader(NhaC587Loader):
    """Load NHA C359 records from harvested Memorix JSON files."""

    source_label = "NHA C359"
    collection_dir = "c359"
