#!/usr/bin/env python3
"""
NLUX-Carousell Backend Server

Provides a carousel API that randomly selects objects from a collection
and serves them with full-screen display support.

Usage:
    python server.py --port 8089 --collection teylers
    python server.py --port 8089 --collection item --config myconfig.json
"""

import json
import os
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Any

from fastapi import FastAPI, Query, Request, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import aiohttp


# Settings
class Settings(BaseSettings):
    PORT: int = 8089
    HOST: str = "0.0.0.0"
    COLLECTION: str = "teylers"
    CONFIG_PATH: str = "config/current.json"
    DEFAULT_CONFIG: str = "config/default.json"
    NLUX_API: str = "http://localhost:8000"
    NLUX_API_TOKEN: Optional[str] = None
    TIMEOUT: float = 30.0
    DEFAULT_SEED: Optional[str] = None
    
    # Carousel settings
    INTERVAL: int = 10  # seconds between slides
    COUNT: int = 5  # objects per slide
    MAX_AGE: int = 30  # seconds before forcing reseed
    
    # Collections
    AVAILABLE_COLLECTIONS: list[str] = []
    
    # Default config
    def __post_init__(self):
        if not os.path.exists(self.CONFIG_PATH):
            self.load_default_config()
            
        # Load available collections from NLUX API
        if os.getenv("ENABLE_COLLECTIONS", "true").lower() == "true":
            self.load_collections()

class CarouselItem(BaseModel):
    """Individual carousel slide data"""
    uri: str
    uri_short: str
    scope: str
    label: str
    title: Optional[str] = None
    creator: Optional[str] = None
    creator_name: Optional[str] = None
    date: Optional[str] = None
    media_type: Optional[str] = None
    thumbnail: Optional[str] = None
    full_url: Optional[str] = None
    description: Optional[str] = None
    language: str = "en"
    display_order: int = 0
    added_at: str = ""
    object_number: Optional[str] = None
    location: Optional[str] = None
    material: Optional[str] = None
    technique: Optional[str] = None


class CarouselSlide(BaseModel):
    """A slide containing multiple carousel items"""
    index: int
    items: list[CarouselItem]
    slide_number: int


class CarouselResponse(BaseModel):
    """Full carousel response with all slides"""
    seed: str
    total_slides: int
    slides: list[CarouselSlide]
    next_refresh: str
    last_updated: str


# Initialize FastAPI app
app = FastAPI(
    title="NLUX-Carousell API",
    description="Museum carousel display API - shows random collection objects",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def load_config() -> Settings:
    """Load configuration from file or use defaults"""
    settings = Settings()
    
    if os.path.exists(settings.CONFIG_PATH):
        config_data = json.load(open(settings.CONFIG_PATH))
        for key, value in config_data.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
    
    return settings


# Singleton settings instance
settings = load_config()


# Initialize NLUX API session
nlux_session = None


def get_nlux_api() -> aiohttp.ClientSession:
    """Get or create NLUX API session"""
    global nlux_session
    
    if nlux_session is None:
        headers = {}
        if settings.NLUX_API_TOKEN:
            headers["Authorization"] = f"Bearer {settings.NLUX_API_TOKEN}"
            
        timeout = aiohttp.Timeout(total=settings.TIMEOUT)
        nlux_session = aiohttp.ClientSession(
            headers=headers,
            timeout=timeout
        )
    
    return nlux_session


async def fetch_nlux_record(uri: str) -> dict:
    """Fetch a record from NLUX API"""
    async with get_nlux_api() as session:
        url = f"{settings.NLUX_API}/data/{uri}"
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            return {"error": f"Failed to fetch: {str(e)}"}


async def generate_random_objects(
    count: int,
    scope: str,
    collection: str,
    seed: Optional[str] = None,
    max_age: Optional[int] = None
) -> dict:
    """Generate random objects from collection"""
    return_code = random.getstate()
    
    # Apply seed if provided
    if seed:
        random.setstate(seed)
    
    # Filter for collection
    collection_prefix = f"{collection}/"
    prefix_match = []
    no_prefix = []
    
    # Get object count estimate
    estimate_url = f"{settings.NLUX_API}/api/search-estimate/{scope}?collection={collection}"
    try:
        async with get_nlux_api() as session:
            async with session.get(estimate_url) as est:
                est_data = await est.json()
                total = est_data.get("totalItems", 0)
                estimated = min(count, total)
    except Exception:
        estimated = count
    
    # Generate random URIs
    selected_uris = set()
    attempts = 0
    max_attempts = count * 10
    
    while len(selected_uris) < min(count, estimated) and attempts < max_attempts:
        random_obj_id = random.randint(1, 10000)
        random_obj = f"{collection_prefix}{random_obj_id}"
        
        if random_obj not in selected_uris:
            selected_uris.add(random_obj)
        
        attempts += 1
    
    # Fetch records
    records = []
    for uri in selected_uris:
        data = await fetch_nlux_record(uri)
        if isinstance(data, dict) and "error" not in data:
            records.append(data)
    
    # Reset random state
    random.setstate(return_code)
    
    # Filter by scope
    filtered = []
    for rec in records:
        record_type = rec.get("@type", [])
        if isinstance(record_type, list):
            type_values = [t.get("@value", "") for t in record_type if isinstance(t, dict)]
        else:
            type_values = [record_type.get("@value", "")] if isinstance(record_type, dict) else []
        
        if scope in type_values:
            filtered.append(rec)
    
    # Limit to count
    return {
        "objects": filtered[:count],
        "count": count,
        "actually_fetched": len(filtered),
        "seed": random.getstate()
    }


@app.get("/api/seed")
async def generate_seed():
    """Generate a new random seed"""
    return {"seed": str(uuid.uuid4())}


@app.post("/api/generate")
async def generate_carousel(
    config: dict = Query(..., description="Carousel configuration"),
):
    """Generate carousel with random objects"""
    count = config.get("count", 5)
    scope = config.get("scope", "item")
    collection = config.get("collection", settings.COLLECTION)
    seed = config.get("seed")
    
    # Validate collection exists
    if not os.getenv("ENABLE_COLLECTIONS", "true").lower() == "true":
        collections = [
            "all",
            "taylor",
            "teylers",
            "rma",
            "nha",
            "wfm",
            "fhm",
            "hvh",
            "nha",
        ]
        if collection not in collections:
            raise HTTPException(
                status_code=400,
                detail=f"Collection '{collection}' not available. Use one of: {', '.join(collections)}"
            )
    
    result = await generate_random_objects(count, scope, collection, seed)
    
    return {
        "seed": result["seed"],
        "requested": count,
        "available": result["actually_fetched"],
        "objects": [normalize_object(obj, collection) for obj in result["objects"]]
    }


@app.get("/api/generate")
async def generate_carousel_endpoint(
    count: int = Query(default=5, ge=1, le=50),
    scope: str = Query(default="item"),
    collection: str = Query(default="teylers"),
    seed: Optional[str] = Query(default=None),
):
    """Generate carousel with random objects via GET"""
    return await generate_carousel(config={
        "count": count,
        "scope": scope,
        "collection": collection,
        "seed": seed
    })


@app.post("/api/generate-seed/{seed}")
async def generate_with_seed(seed: str, count: int = 5):
    """Generate carousel using a specific seed"""
    result = await generate_random_objects(count, "item", settings.COLLECTION, seed)
    return result


@app.get("/data/{uri:path}")
async def get_record(uri: str, profile: str = Query("search")):
    """Fetch a single record from NLUX API"""
    return await fetch_nlux_record(uri)


@app.get("/api/collections")
async def get_collections():
    """Get available collection names"""
    if not os.getenv("ENABLE_COLLECTIONS", "true").lower() == "true":
        return {
            "collections": [
                "all",  # All available collections
                "taylor",  # Taylor Institution (University of Oxford)
                "teylers",  # Teylers Museum
                "rma",  # Rijksmuseum (partial Adlib)
                "wfm",  # Worldwide Museums Foundation
                "fhm",  # Flanders Heritage Agents
                "hvh",  # Herencia Virtual de las Humanidades
                "nha",  # Nationale Historische Archief
            ]
        }
    
    # Get from NLUX API
    try:
        async with get_nlux_api() as session:
            url = f"{settings.NLUX_API}/api/stats"
            async with session.get(url) as response:
                data = await response.json()
                return {
                    "collections": [
                        {
                            "name": name,
                            "item_count": item_count,
                            "enabled": True
                        }
                        for name, item_count in data.get("estimates", {}).get("searchScopes", {}).items()
                        if item_count > 0
                    ]
                }
    except Exception as e:
        return {"collections": [], "error": str(e)}


def normalize_object(obj: dict, collection: str) -> CarouselItem:
    """Normalize a fetched object into carousel item format"""
    uri = obj.get("@id", "")
    
    # Extract basic fields
    label = extract_field(obj, ["label"], "en")
    title = extract_field(obj, ["title"])
    creator = extract_field(obj, ["creator"])
    creator_name = extract_field(obj, ["creator.name"], [])
    date = extract_field(obj, ["production.date.start"])
    media_type = extract_field(obj, ["hasMediaType"])
    location = extract_field(obj, ["location.default.name"])
    material = extract_field(obj, ["material"])
    technique = extract_field(obj, ["technique"])
    description = extract_field(obj, ["description"])
    object_number = extract_field(obj, ["object_number"])
    
    # Build labels
    labels = {}
    if isinstance(label, list):
        labels = label
    elif isinstance(label, dict):
        labels = [label]
    else:
        labels = [str(label)]
    
    # Build metadata
    metadata = {
        "title": list(title) if title else None,
        "hasCreator": list(creator) if creator else None,
        "hasDate": date,
        "hasMediaType": media_type,
        "hasLocation": location,
        "hasMaterial": material,
        "hasTechnique": technique,
    }
    
    # Extract thumbnail
    thumbnail = None
    has_img = False
    
    if "hasImage" in obj or "image" in obj:
        has_img = True
        for href_obj in obj.get("hasImage", []):
            if isinstance(href_obj, dict):
                for link in href_obj.get("hasWebOrEmbeddedResource", []):
                    if isinstance(link, dict) and "rel" in link:
                        thumbnail = link.get("@id")
                        break
            elif isinstance(href_obj, str):
                thumbnail = href_obj
                break
    
    # Build full URL
    full_url = None
    if "hasImage" in obj:
        for href_obj in obj.get("hasImage", []):
            for link in href_obj.get("hasWebOrEmbeddedResource", []):
                if isinstance(link, dict) and "rel" in link:
                    full_url = link.get("@id")
                    break
    
    return CarouselItem(
        uri=uri,
        uri_short=uri.split("/")[-1] if uri else "",
        scope="item",
        label=labels[0] if labels else "Untitled",
        title=title if title else None,
        creator=list(creator)[0] if creator and len(creator) > 0 else None,
        creator_name=creator_name if creator_name else None,
        date=date,
        media_type=media_type,
        thumbnail=thumbnail,
        full_url=full_url,
        description=description[:500] if description and len(description) > 500 else description,
        language="en",
        display_order=0,
        added_at=datetime.utcnow().isoformat(),
        object_number=object_number,
    )


def extract_field(obj: dict, path: list, default=None):
    """Extract field value from nested object structure"""
    value = obj
    for key in path:
        if isinstance(value, dict):
            value = value.get(key)
            if value is None:
                return default
        elif isinstance(value, list):
            if key.isdigit():
                index = int(key)
                value = value[index] if index < len(value) else default
                break
            elif key == "*":
                value = [v for v in value if v is not None]
        else:
            return default
    return value


if __name__ == "__main__":
    import uvicorn
    
    # Initialize
    settings = load_config()
    
    # Check for NLUX API
    if settings.NLUX_API:
        # Verify connection
        try:
            import urllib.request
            urllib.request.urlopen(f"{settings.NLUX_API}/health", timeout=5)
            print(f"✓ Connected to NLUX API at {settings.NLUX_API}")
        except urllib.error.URLError as e:
            print(f"⚠ Warning: Could not connect to NLUX API ({settings.NLUX_API})")
            print("  The carousell will only work with local collection data")
            os.environ["ENABLE_COLLECTIONS"] = "false"
            settings = load_config()
    
    uvicorn.run(
        "server:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True if os.getenv("DEV", "false") == "true" else False,
    )
