# nlux-carousel

A full-screen carousel display for NLUX collections (**Teylers Museum** and
**Noord-Hollands Archief** so far). It shows a random, changing selection of
objects with images from the nlux backend API.

```
nlux backend (:8000)                    carousel server (:8089)
GET /api/search/{scope}                 GET /api/carousel   random image-bearing objects
GET /data/{uri}           <------------ GET /api/config     carousel + theme config
GET /iiif/image/{token}                 GET /health        liveness of server + backend
                                        + serves caroussel/frontend/dist (production)

caroussel/frontend (Vite, vanilla JS)
  src/CarouselApp.js       controller: fetch config/items, timers, fullscreen, keyboard
  src/components/Carousel.js  renderer: slides, captions, progress bar, swipe, pause
  src/VanillaSettingsModal.js  settings dialog (interval, count, scope)
  styles/carousel.css      light kiosk theme (CSS vars from config theme)
  test/smoke.mjs          jsdom smoke test (npm test)
```

## Run it

```bash
# 1. Load Teylers objects (with images) into the backend DB
make carousel-load                 # maps 200 random image-bearing Teylers objects
make carousel-load-nha             # maps 400 random image+title NHA objects

# 2. Start backend + carousel server together (builds the frontend first)
make carousel-run                  # then open http://localhost:8089/

# Or run the parts separately:
make backend-run                   # nlux API on :8000
cd caroussel/server && uv run --python 3.12 --with-requirements requirements.txt python server.py
cd caroussel/frontend && npm run dev   # vite dev server on :5173 (proxies /api and /iiif)
```

## How it works

1. **Data** — `backend/scripts/load_teylers_from_raw.py` feeds raw Adlib
   harvest records (`$LUX_BASEPATH/data/input/teylers`) through the real
   data-pipeline mapper (`pipeline/sources/museums/teylers/mapper.py`), which
   produces Linked Art JSON **including image representations** and IIIF
   manifests. Only records with a public web image are selected; the result
   is loaded into the backend database.

2. **Carousel server** (`caroussel/server/server.py`) queries the backend
   with the structured search `{"hasDigitalImage": true}`, samples random
   objects, fetches each record and normalises it into a slide item
   (title, creator, date, technique, materials, accession number, image).
   Images are served through the backend's trusted `/iiif/image/{token}`
   proxy (`teylers.adlibhosting.com`).

3. **Frontend** — vanilla JS, no framework. After each full cycle it fetches
   a fresh batch of objects. Controls: `←`/`→` navigate, space pauses,
   `F` fullscreen, `S` settings. Settings (interval, object count, scope)
   persist in `localStorage`.

## URL parameters

| Parameter | Example | Effect |
|-----------|---------|--------|
| `collection` | `http://localhost:8089/?collection=teylers` | Selects which collection to display (name from the `collections` config block). Without it, the configured `default_collection` is used. The brand subtitle in the top bar shows the collection label. |
| `api` | `/?api=http://localhost:8089` | Point the frontend at another carousel server. |

Unknown collection names result in an error screen listing the available
collections.

## Configuration

`caroussel/config/default.json` — server port, carousel interval/count,
named `collections` (per collection: `label` for the top bar, `scope`,
`query` for the backend search filter) plus `default_collection` and theme
colors. Adding a second institution is a matter of adding a block:

```json
"collections": {
  "teylers": {
    "label": "Teylers Museum",
    "scope": "item",
    "query": { "hasDigitalImage": true },
    "uri_prefix": "https://teylers.adlibhosting.com/nlux/",
    "credit": "Teylers Museum, Haarlem"
  },
  "nha": {
    "label": "Noord-Hollands Archief",
    "scope": "item",
    "query": { "hasDigitalImage": true },
    "uri_prefix": "https://hdl.handle.net/21.12102/",
    "credit": "Noord-Hollands Archief, Haarlem"
  }
}
```

`uri_prefix` restricts a collection to one institution's URI namespace, so
several collections can share a single backend database. `credit` is the
holding institution shown under each slide (falls back to the collection
label). NHA records are
loaded with `make carousel-load-nha` (raw Memorix harvests in
`$LUX_BASEPATH/data/input/nha/{c1477,c359,c480,c587}` through the
data-pipeline's NhaMapper, images via the `images.memorix.nl` proxy).

Environment overrides for the server: `NLUX_API` (default
`http://localhost:8000`), `CAROUSEL_CONFIG` (config path).

## Tests

```bash
make carousel-test   # jsdom smoke test: boots the app against a mocked API
```