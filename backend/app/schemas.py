from typing import Any
from pydantic import BaseModel


class SearchResult(BaseModel):
    id: str
    type: str
    label: str | None


class SearchResponse(BaseModel):
    """Mirrors lux-middletier search response format."""
    context: str = "https://linked.art/ns/v1/linked-art.json"
    id: str
    type: str = "OrderedCollectionPage"
    totalItems: int
    orderedItems: list[dict[str, Any]]
