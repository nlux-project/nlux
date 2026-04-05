from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class SearchResult(BaseModel):
    id: str
    type: str
    label: Optional[str]


class SearchResponse(BaseModel):
    """Mirrors lux-middletier search response format."""
    context: str = "https://linked.art/ns/v1/linked-art.json"
    id: str
    type: str = "OrderedCollectionPage"
    totalItems: int
    orderedItems: List[Dict[str, Any]]
    partOf: List[Dict[str, Any]] = []
