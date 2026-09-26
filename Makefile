# =========================================================================
# NLUX — top-level task runner
#
# LUX_BASEPATH : data storage root used by the data-pipeline
#                (harvested input, datacache, exports and config_cache)
#                  default: /Users/lux/data-pipeline   (macOS)
#                           /home/lux/data-pipeline    (Linux)
#                Override: make <target> LUX_BASEPATH=/path/to/storage
#
# make install VOLUME=/Volumes/<disk>
#     Symlinks $(LUX_BASEPATH)/data/output -> $(VOLUME)/data so heavy
#     pipeline output lives on an external data volume.
#
# Pipeline knobs:
#     make reconcile SOURCE=teylers    pick the collection source
#     make export    SLICE=2 MAXSLICE=8   run one parallel slice
#
# Run `make help` for the full target list.
# =========================================================================

SHELL := /bin/bash
.DEFAULT_GOAL := help

# --- Environment -----------------------------------------------------------

UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Darwin)
DEFAULT_LUX_BASEPATH := /Users/lux/data-pipeline
else
DEFAULT_LUX_BASEPATH := /home/lux/data-pipeline
endif

LUX_BASEPATH ?= $(DEFAULT_LUX_BASEPATH)
export LUX_BASEPATH

# Backend code requires Python >= 3.10 (PEP 604 unions); the API Docker image
# uses 3.12, so pin the uv-managed interpreter to match. uv resolves and
# caches each requirements.txt on first use.
PYTHON_VERSION ?= 3.12

# Carousel display (caroussel/) knobs
CAROUSEL_COUNT ?= 200
CAROUSEL_SEED ?= 42
CAROUSEL_NHA_COUNT ?= 400
CAROUSEL_NHA_SEED ?= 42
CAROUSEL_HVH_COUNT ?= 400
CAROUSEL_HVH_SEED ?= 42
CAROUSEL_FHM_COUNT ?= 400
CAROUSEL_FHM_SEED ?= 42
CAROUSEL_WFM_COUNT ?= 400
CAROUSEL_WFM_SEED ?= 42
CAROUSEL_RMA_COUNT ?= 400
CAROUSEL_RMA_SEED ?= 42
CAROUSEL_RBHC_COUNT ?= 400
CAROUSEL_RBHC_SEED ?= 42

# Run from repo root; requirements path relative to root.
BACKEND_PY := uv run --python $(PYTHON_VERSION) --with-requirements backend/requirements.txt python

# Run from inside data-pipeline/; requirements path relative to that dir.
PIPELINE_PY := uv run --python $(PYTHON_VERSION) --with-requirements requirements.txt python

# --- Knobs -----------------------------------------------------------------

# Pipeline collection source to process (teylers, fhm, hvh, rbhc, wfm, ...)
SOURCE ?= teylers
# Parallel slice control for reconcile / merge / export
SLICE ?= 0
MAXSLICE ?= 1
# Pipeline export location used by api-load
EXPORT_DIR ?= $(LUX_BASEPATH)/data/output/latest

# --- Meta ------------------------------------------------------------------

.PHONY: help
help:
	@printf '\n'
	@printf 'Setup ======================================================================\n'
	@printf '  install                 symlink $$(LUX_BASEPATH)/data/output to an external disk\n'
	@printf '                          (usage: make install VOLUME=/Volumes/<disk>)\n\n'
	@printf 'Backend (FastAPI API) =======================================================\n'
	@printf '  backend-install         provision the pinned Python env for backend/requirements.txt\n'
	@printf '  backend-run             run the API dev server on :8000 (uvicorn --reload)\n'
	@printf '  backend-reset           drop and recreate the API database\n'
	@printf '  api-load                load exported Linked Art JSONL into the API DB\n'
	@printf '                          (EXPORT_DIR=$$(LUX_BASEPATH)/data/output/latest)\n'
	@printf '  api-generate-agents     generate Person/Group records from object data\n'
	@printf '  api-generate-concepts   generate concept records from object data\n\n'
	@printf 'Data pipeline ==============================================================\n'
	@printf '  pipeline-install        provision the pinned Python env for data-pipeline/requirements.txt\n'
	@printf '  harvest-teylers         step 1: harvest Teylers records from the Adlib API\n'
	@printf '  pipeline-load           step 2: load harvested records into the datacache (SOURCE=teylers)\n'
	@printf '  reconcile               step 3: reconcile against authority data (SOURCE, SLICE, MAXSLICE)\n'
	@printf '  merge                   step 4: merge/deduplicate entities (SOURCE, SLICE, MAXSLICE)\n'
	@printf '  export                  step 5: export Linked Art JSONL (SLICE, MAXSLICE)\n'
	@printf '  pipeline                steps 1-5 in sequence for SOURCE=teylers\n'
	@printf '  pipeline-sync           update $$(LUX_BASEPATH) working tree with repo pipeline code\n'
	@printf '                          (update-only; DRY_RUN=1 previews; data/ untouched)\n'
	@printf '  harvest-aat             harvest AAT authority data (run once before first reconcile)\n'
	@printf '  index-aat               load AAT into the reference index (after harvest-aat)\n\n'
	@printf 'Testing ====================================================================\n'
	@printf '  test-backend            backend test suite (container tests need the API container up)\n'
	@printf '  test-pipeline           data-pipeline unit tests (mappers, exporters)\n'
	@printf '  test-pipeline-integration  per-source validation suites (needs live services)\n'
	@printf '  test-frontend           frontend unit + integration tests (vitest)\n'
	@printf '  test                    all of the above\n\n'
	@printf 'Docker =====================================================================\n'
	@printf '  docker-up               start api + frontend (compose up)\n'
	@printf '  docker-up-pipeline      also start PostgreSQL + Redis (pipeline profile)\n'
	@printf '  docker-down             stop all compose services\n'
	@printf '  docker-load-all         load all Teylers data into the running API container\n\n'
	@printf 'Frontend ===================================================================\n'
	@printf '  frontend-install        npm ci (use after cloning / pulling)\n'
	@printf '  frontend-dev            vite dev server\n'
	@printf '  frontend-build          type-check + production build\n'
	@printf '  frontend-lint           eslint\n\n'
	@printf 'Carousel display (caroussel/) ===============================================\n'
	@printf '  carousel-install        npm ci for the carousel frontend\n'
	@printf '  carousel-build          production build (served by the carousel server)\n'
	@printf '  carousel-dev            vite dev server on :5173 (proxies /api)\n'
	@printf '  carousel-run            start backend :8000 + carousel server :8089\n'
	@printf '  carousel-test           jsdom smoke test of the carousel frontend\n'
	@printf '  carousel-load           (re)map Teylers objects with images into the API DB\n'
	@printf '                          (CAROUSEL_COUNT=200 CAROUSEL_SEED=42)\n'
	@printf '  carousel-load-nha       map Noord-Hollands Archief objects into the API DB\n'
	@printf '                          (CAROUSEL_NHA_COUNT=400 CAROUSEL_NHA_SEED=42)\n'
	@printf '  carousel-load-hvh       map Huis van Hilde objects into the API DB\n'
	@printf '                          (CAROUSEL_HVH_COUNT=400 CAROUSEL_HVH_SEED=42)\n'
	@printf '  carousel-load-fhm       map Frans Hals Museum objects into the API DB\n'
	@printf '                          (CAROUSEL_FHM_COUNT=400 CAROUSEL_FHM_SEED=42)\n'
	@printf '  carousel-load-wfm       map Westfries Museum objects into the API DB\n'
	@printf '                          (CAROUSEL_WFM_COUNT=400 CAROUSEL_WFM_SEED=42)\n'
	@printf '  carousel-load-rma       map Rijksmuseum objects into the API DB\n'
	@printf '                          (CAROUSEL_RMA_COUNT=400 CAROUSEL_RMA_SEED=42)\n'
	@printf '  carousel-load-rbhc       map Rijksmuseum Boerhaave objects into the API DB\n'
	@printf '                          (CAROUSEL_RBHC_COUNT=400 CAROUSEL_RBHC_SEED=42)\n\n'
	@printf 'Docs =======================================================================\n'
	@printf '  docs-serve              mkdocs local preview on :8001\n'
	@printf '  docs-deploy             deploy docs to GitHub Pages\n\n'
	@printf 'Knobs (override on the command line):\n'
	@printf '  LUX_BASEPATH=<path>     data storage root   (default: $(LUX_BASEPATH))\n'
	@printf '  PYTHON_VERSION=<ver>    interpreter pin     (default: $(PYTHON_VERSION))\n'
	@printf '  SOURCE=<source>          pipeline collection  (default: $(SOURCE))\n'
	@printf '  SLICE=<n> MAXSLICE=<n>   parallel slice control (default: $(SLICE) / $(MAXSLICE))\n'
	@printf '  EXPORT_DIR=<path>       export location for api-load (default: $(EXPORT_DIR))\n'
	@printf '  CAROUSEL_COUNT=<n>      objects to map for the carousel (default: $(CAROUSEL_COUNT))\n'
	@printf '  CAROUSEL_SEED=<n>       sampling seed for carousel-load (default: $(CAROUSEL_SEED))\n\n'

# --- Storage setup ----------------------------------------------------------

.PHONY: install
install:
	@test -n "$(VOLUME)" || { echo "usage: make install VOLUME=/Volumes/<external-disk>"; exit 2; }
	@if [ -e "$(LUX_BASEPATH)/data/output" ] && [ ! -L "$(LUX_BASEPATH)/data/output" ]; then \
		echo "refusing: $(LUX_BASEPATH)/data/output exists and is not a symlink"; exit 1; \
	fi
	@test -e "$(VOLUME)/data" || echo "note: $(VOLUME)/data does not exist yet — it will be created on first write"
	mkdir -p "$(LUX_BASEPATH)/data"
	ln -sfn "$(VOLUME)/data" "$(LUX_BASEPATH)/data/output"
	@echo "$(LUX_BASEPATH)/data/output -> $(VOLUME)/data"

# --- Backend ----------------------------------------------------------------

.PHONY: backend-install
backend-install:
	cd backend && uv run --python $(PYTHON_VERSION) --with-requirements requirements.txt \
		python -c "import fastapi, sqlalchemy, pydantic_settings; print('backend environment ready (python $(PYTHON_VERSION))')"

.PHONY: backend-run
backend-run:
	cd backend && uv run --python $(PYTHON_VERSION) --with-requirements requirements.txt \
		uvicorn app.main:app --reload

.PHONY: backend-reset
backend-reset:
	$(BACKEND_PY) backend/scripts/reset.py

.PHONY: api-load
api-load:
	$(BACKEND_PY) backend/scripts/load_data.py "$(EXPORT_DIR)"

.PHONY: api-generate-agents
api-generate-agents:
	$(BACKEND_PY) backend/scripts/generate_agents.py

.PHONY: api-generate-concepts
api-generate-concepts:
	$(BACKEND_PY) backend/scripts/generate_concepts.py

# --- Data pipeline ------------------------------------------------------------

.PHONY: pipeline-install
pipeline-install:
	cd data-pipeline && $(PIPELINE_PY) -c "import dotenv, psycopg2, redis, ujson; print('pipeline environment ready (python $(PYTHON_VERSION))')"

.PHONY: harvest-teylers
harvest-teylers:
	cd data-pipeline && mkdir -p data/input/teylers && \
		$(PIPELINE_PY) ./harvest-teylers.py data/input/teylers

.PHONY: harvest-aat
harvest-aat:
	cd data-pipeline && $(PIPELINE_PY) ./run-harvest.py --aat

.PHONY: index-aat
index-aat:
	cd data-pipeline && $(PIPELINE_PY) ./manage-data.py --load-index --aat

.PHONY: pipeline-load
pipeline-load:
	cd data-pipeline && $(PIPELINE_PY) ./manage-data.py --load --$(SOURCE)

.PHONY: reconcile
reconcile:
	cd data-pipeline && $(PIPELINE_PY) ./run-reconcile.py $(SLICE) $(MAXSLICE) --$(SOURCE)

.PHONY: merge
merge:
	cd data-pipeline && $(PIPELINE_PY) ./run-merge.py $(SLICE) $(MAXSLICE) --$(SOURCE)

.PHONY: export
export:
	cd data-pipeline && $(PIPELINE_PY) ./run-export.py $(SLICE) $(MAXSLICE)

# Sync pipeline code from this repo to the $(LUX_BASEPATH) working tree
# (the tree where harvests run and data/ lives). Update-only: overwrites
# changed code files with the repo versions, never deletes anything and
# never touches data/ or local-only files. Preview: make pipeline-sync DRY_RUN=1
ifeq ($(DRY_RUN),1)
SYNC_DRY := --dry-run
endif
RSYNC := rsync -a --itemize-changes $(SYNC_DRY)

.PHONY: pipeline-sync
pipeline-sync:
	@if [ "$$(cd "$(LUX_BASEPATH)" 2>/dev/null && pwd)" = "$$(cd data-pipeline && pwd)" ]; then \
		echo "pipeline-sync: refusing to sync onto the repo itself (LUX_BASEPATH=$(LUX_BASEPATH))"; exit 1; fi
	mkdir -p "$(LUX_BASEPATH)"
	$(RSYNC) --exclude='__pycache__/' --exclude='*.pyc' data-pipeline/pipeline/ "$(LUX_BASEPATH)/pipeline/"
	$(RSYNC) --exclude='__pycache__/' --exclude='*.pyc' data-pipeline/tests/ "$(LUX_BASEPATH)/tests/"
	$(RSYNC) --exclude='__pycache__/' --exclude='*.pyc' data-pipeline/docs/ "$(LUX_BASEPATH)/docs/"
	$(RSYNC) data-pipeline/*.py data-pipeline/*.sh data-pipeline/*.json data-pipeline/*.md \
		data-pipeline/Makefile data-pipeline/LICENSE data-pipeline/requirements.txt data-pipeline/requirements_dev.txt \
		"$(LUX_BASEPATH)/"
	@echo "pipeline code synced to $(LUX_BASEPATH)$(if $(SYNC_DRY), (dry run — nothing written),)"

.PHONY: pipeline
pipeline: harvest-teylers pipeline-load reconcile merge export

# --- Testing -------------------------------------------------------------------

.PHONY: test-backend
test-backend:
	bash backend/tests/test-backend.sh

.PHONY: test-pipeline
test-pipeline:
	cd data-pipeline && $(PIPELINE_PY) -m unittest tests.test_agent_export tests.test_biography_enrichment tests.test_entity_export tests.test_export_splitting tests.test_teylers_pipeline.TeylersPipelineIntegrationTest.test_mapper_extracts_portrait_subject_person

# Full per-source validation suites: expect a live pipeline environment
# (PostgreSQL + Redis via `make docker-up-pipeline`) and $LUX_BASEPATH data.
.PHONY: test-pipeline-integration
test-pipeline-integration:
	bash data-pipeline/tests/test_all.sh

.PHONY: test-frontend
test-frontend:
	cd frontend/client && npm test

.PHONY: test
test: test-backend test-pipeline test-frontend carousel-test

# --- Docker --------------------------------------------------------------------

.PHONY: docker-up
docker-up:
	docker compose up

.PHONY: docker-up-pipeline
docker-up-pipeline:
	docker compose --profile pipeline up

.PHONY: docker-down
docker-down:
	docker compose down

.PHONY: docker-load-all
docker-load-all:
	bash backend/scripts/load_all_to_docker.sh

# --- Frontend --------------------------------------------------------------------

.PHONY: frontend-install
frontend-install:
	cd frontend/client && npm ci --legacy-peer-deps

.PHONY: frontend-dev
frontend-dev:
	cd frontend/client && npm start

.PHONY: frontend-build
frontend-build:
	cd frontend/client && npm run build

.PHONY: frontend-lint
frontend-lint:
	cd frontend/client && npm run lint

# --- Carousel display ------------------------------------------------------------

.PHONY: carousel-install
carousel-install:
	cd caroussel/frontend && npm ci

.PHONY: carousel-build
carousel-build:
	cd caroussel/frontend && npm run build

.PHONY: carousel-dev
carousel-dev:
	cd caroussel/frontend && npm run dev

.PHONY: carousel-test
carousel-test:
	cd caroussel/frontend && npm test

.PHONY: carousel-run
carousel-run:
	$(MAKE) -s carousel-build
	@echo 'Starting backend :8000 and carousel server :8089 ...'
	@bash -c '\
		trap "kill 0" EXIT; \
		(cd backend && uv run --python $(PYTHON_VERSION) --with-requirements requirements.txt python -m uvicorn app.main:app --port 8000) & \
		(cd caroussel/server && uv run --python $(PYTHON_VERSION) --with-requirements requirements.txt python server.py) & \
		wait'

.PHONY: carousel-load
carousel-load:
	cd backend && uv run --python $(PYTHON_VERSION) --with-requirements requirements.txt \
		--with-requirements ../data-pipeline/requirements.txt \
		python scripts/load_teylers_from_raw.py \
		--count $(CAROUSEL_COUNT) --seed $(CAROUSEL_SEED) --reset

.PHONY: carousel-load-nha
carousel-load-nha:
	cd backend && uv run --python $(PYTHON_VERSION) --with-requirements requirements.txt \
		--with-requirements ../data-pipeline/requirements.txt \
		python scripts/load_nha_from_raw.py \
		--count $(CAROUSEL_NHA_COUNT) --seed $(CAROUSEL_NHA_SEED)

.PHONY: carousel-load-hvh
carousel-load-hvh:
	cd backend && uv run --python $(PYTHON_VERSION) --with-requirements requirements.txt \
		--with-requirements ../data-pipeline/requirements.txt \
		python scripts/load_hvh_from_raw.py \
		--count $(CAROUSEL_HVH_COUNT) --seed $(CAROUSEL_HVH_SEED)

.PHONY: carousel-load-fhm
carousel-load-fhm:
	cd backend && uv run --python $(PYTHON_VERSION) --with-requirements requirements.txt \
		--with-requirements ../data-pipeline/requirements.txt \
		python scripts/load_fhm_from_raw.py \
		--count $(CAROUSEL_FHM_COUNT) --seed $(CAROUSEL_FHM_SEED)

.PHONY: carousel-load-wfm
carousel-load-wfm:
	cd backend && uv run --python $(PYTHON_VERSION) --with-requirements requirements.txt \
		--with-requirements ../data-pipeline/requirements.txt \
		python scripts/load_wfm_from_raw.py \
		--count $(CAROUSEL_WFM_COUNT) --seed $(CAROUSEL_WFM_SEED)

.PHONY: carousel-load-rma
carousel-load-rma:
	cd backend && uv run --python $(PYTHON_VERSION) --with-requirements requirements.txt \
		python scripts/load_rma_from_raw.py \
		--count $(CAROUSEL_RMA_COUNT) --seed $(CAROUSEL_RMA_SEED)

.PHONY: carousel-load-rbhc
carousel-load-rbhc:
	cd backend && uv run --python $(PYTHON_VERSION) --with-requirements requirements.txt \
		--with-requirements ../data-pipeline/requirements.txt \
		python scripts/load_rbhc_from_raw.py \
		--count $(CAROUSEL_RBHC_COUNT) --seed $(CAROUSEL_RBHC_SEED)

# --- Docs -----------------------------------------------------------------------

.PHONY: docs-serve
docs-serve:
	uv run --python $(PYTHON_VERSION) --with mkdocs --with mkdocs-material mkdocs serve

.PHONY: docs-deploy
docs-deploy:
	uv run --python $(PYTHON_VERSION) --with mkdocs --with mkdocs-material mkdocs gh-deploy --force