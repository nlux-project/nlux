# nlux-carousel

A full-screen carousel display for NLUX collections (currently **Teylers
Museum**). It shows a random, changing selection of objects with images from
the nlux backend API.

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
  styles/carousel.css      dark kiosk theme (CSS vars from config theme)
  test/smoke.mjs          jsdom smoke test (npm test)
```

## Run it

```bash
# 1. Load Teylers objects (with images) into the backend DB
make carousel-load                 # maps 200 random image-bearing objects

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

## Configuration

`caroussel/config/default.json` — server port, carousel interval/count,
collection scope, theme colors. Environment overrides for the server:
`NLUX_API` (default `http://localhost:8000`), `CAROUSEL_CONFIG` (config path).

## Tests

```bash
make carousel-test   # jsdom smoke test: boots the app against a mocked API
```