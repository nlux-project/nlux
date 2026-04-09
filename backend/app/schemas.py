from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class SearchResult(BaseModel):
    """Activity Streams stub returned in orderedItems."""
    id: str
    type: str
