from pipeline.sources.museums.nha.c587.loader import NhaC587Loader


class NhaC480Loader(NhaC587Loader):
    """Load NHA C480 records from harvested Memorix JSON files."""

    source_label = "NHA C480"
    collection_dir = "c480"
