# NLUX Technical Implementation Plan

**Version:** 0.2.0-draft  
**Date:** 2026-04-04  
**Status:** Draft

---

## 1. Overview

NLUX (Nederlandse Linked Data Uitwisseling / NL Collections Discovery) is a collections discovery platform for the Dutch Cultural Heritage sector. It is built on top of Yale University's [LUX: Yale Collections Discovery](https://lux.collections.yale.edu/) platform and reuses as much of LUX's codebase, tooling, and architecture as possible. NLUX must remain 100% compatible with Project LUX — i.e., any LUX dataset should work in NLUX without modification, and vice versa.

---

## 2. LUX Architecture Overview

Understanding the upstream LUX platform is the prerequisite for NLUX. LUX consists of:

| Component | Technology | Repository |
|-----------|-----------|------------|
| Data pipeline | Python, XSLT, shell | [project-lux/lux-data](https://github.com/project-lux/lux-data) |
| Backend search | MarkLogic (NoSQL XML/JSON) | [project-lux/lux-backend](https://github.com/project-lux/lux-backend) |
| Frontend | React / TypeScript | [project-lux/lux-frontend](https://github.com/project-lux/lux-frontend) |
| Documentation | MkDocs / Linked.art | [project-lux/documentation](https://github.com/project-lux/documentation) |
| Data model | Linked.art (CIDOC-CRM) | — |

NLUX will fork or extend each component, applying minimal Dutch-specific customisations.

---

## 3. Goals and Constraints

- **100% LUX compatibility**: data model stays Linked.art / CIDOC-CRM; APIs remain LUX-compatible.
- **Minimal customisation**: prefer configuration over code changes; maintain a thin diff from upstream.
- **Open source**: all NLUX-specific code is published under an OSI-approved licence (Apache 2.0 recommended).
- **Dutch Cultural Heritage focus**: initial target institutions include Teylers Museum, Museum Boerhaave, Huis van Hilde, RMO Leiden.
- **Low cost**: avoid or minimise proprietary/commercial dependencies (especially MarkLogic licensing).

---

## 4. Architecture Decision: Backend — Decision Record

LUX uses MarkLogic as its backend, which is a commercial product. After evaluation, **MarkLogic has been ruled out** for NLUX (see [nlux-project/nlux#10](https://github.com/nlux-project/nlux/issues/10)).

### Decision (2026-04-04): `nlux-backend`

MarkLogic was found to be too complex and overengineered for NLUX's Phase 0 needs. NLUX will use a purpose-built open-source backend:

**`nlux-backend`** — a simplified Python/FastAPI service that:
- Implements the LUX middletier REST API contract (compatible with `lux-frontend` and `lux-middletier`)
- Stores and serves Linked Art JSON-LD records
- Uses **SQLite** in development and **PostgreSQL** in production
- Is fully containerised with Docker

### Rejected options

| Option | Reason rejected |
|--------|----------------|
| MarkLogic Developer licence | Too complex; commercial vendor lock-in; overengineered for initial scope |
| OpenSearch + triplestore | Significant engineering effort deferred to Phase 2+ |

### Future

An OpenSearch evaluation track remains open for Phase 2 if PostgreSQL full-text search proves insufficient at scale.

---

## 5. Component Plan

### 5.1 Data Model

- Adopt Linked.art in full, as documented at [project-lux.github.io/documentation](https://project-lux.github.io/documentation).
- Extend with Dutch-specific vocabularies where needed (e.g. RKDartists, NTA authority files, AAT Dutch labels), always as additions that do not break the core Linked.art shape.
- Use the NLUX documentation site (this MkDocs repo) to document Dutch extensions.

### 5.2 Data Pipeline

- Fork `project-lux/lux-data`.
- Add Dutch institution connectors:
  - RijksmuseuM API (already JSON-LD / Linked.art friendly)
  - Adlib / Axiell EMu XML exports (Teylers, RMO, etc.)
  - OAI-PMH endpoints
- Transformation tooling: Python + XSLT (as upstream); consider adding a [CoGS](https://github.com/linked-art/cogs) pipeline step.
- Output: Linked.art JSON-LD blobs, identical in shape to LUX production data.

### 5.3 Backend

**`nlux-backend`** (repository: [nlux-project/nlux-backend](https://github.com/nlux-project/nlux-backend)) is NLUX's custom backend, replacing `lux-marklogic`.

**Phase 0 (current):** Core API — record retrieval, full-text search, health endpoint.

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Liveness check |
| `GET /data/{uri}` | Retrieve a Linked Art record by URI |
| `GET /api/search/{scope}` | Full-text search with pagination |

**Stack:**

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI (Python 3.12) |
| ORM | SQLAlchemy 2 |
| Database (dev) | SQLite with FTS5 |
| Database (prod) | PostgreSQL with `tsvector` |
| Container | Docker / Docker Compose |

**Phase 2:** Evaluate OpenSearch as a search backend if PostgreSQL FTS proves insufficient at scale.

### 5.4 Frontend

- Fork `project-lux/lux-frontend`.
- Dutch-language translations (i18n): add `nl` locale using LUX's existing i18n mechanism.
- Branding: configure theme colours, logo, and institution list via environment variables / config (no code changes).
- Host: static build deployed to GitHub Pages (initial) → CDN (production).

### 5.5 Infrastructure

| Environment | Platform | Cost |
|-------------|----------|------|
| Development | Local Docker Compose | Free |
| Staging | GitHub Actions CI + GitHub Pages | Free |
| Production (v1) | A cloud provider (Hetzner, AWS, or SURF) | €50–300/mo estimated |
| MarkLogic (if Option A) | MarkLogic Developer (local) or ML Cloud | Free–$500+/mo |

SURF Research Cloud or SURF hosted services are a strong candidate for Dutch academic/cultural heritage projects — explore eligibility.

### 5.6 DevOps & CI/CD

- Git monorepo or multi-repo (mirror LUX's structure).
- GitHub Actions for CI: lint, test, build, deploy.
- Docker Compose for local development of all services.
- Semantic versioning; release notes per component tied to LUX upstream tags.

---

## 6. LUX Upstream Compatibility Strategy

To stay compatible with LUX:

1. Track LUX upstream releases with a dedicated branch (e.g. `upstream/main`).
2. Apply NLUX patches as a thin layer via git cherry-pick or patch files.
3. Run LUX's own test suite against NLUX builds in CI.
4. Participate in the LUX open source community (issues, PRs) where problems affect both.

---

## 7. Data Governance & Standards

- All data published as Linked.art JSON-LD, licenced CC0 or CC-BY where institutions permit.
- Personal data (provenance, collector names): follow AVG/GDPR; no personal data in public endpoints without consent.
- Authority files: align with Wikidata, AAT, RKD, NTA, and VIAF for entity reconciliation.
- Persistent identifiers: use ARK or Handle URIs for NLUX-minted records; institutions retain their own PIDs.

---

## 8. Technology Stack Summary

| Layer | Technology |
|-------|-----------|
| Data model | Linked.art (JSON-LD, CIDOC-CRM) |
| Data pipeline | Python 3.11+, XSLT 2.0, Apache Jena |
| Backend (phase 0–1) | FastAPI + SQLite / PostgreSQL (`nlux-backend`) |
| Backend (phase 2+) | OpenSearch evaluation (optional) |
| Frontend | React 18, TypeScript, LUX frontend fork |
| Documentation | MkDocs + Material theme |
| CI/CD | GitHub Actions |
| Container | Docker / Docker Compose |
| Hosting | GitHub Pages (static), SURF or Hetzner (backend) |
| Licence | Apache 2.0 (code), CC0/CC-BY (data) |

---

## 9. Phased Roadmap

### Phase 0 — Foundation (Months 1–3)
- [ ] Set up GitHub organisation (e.g. `nlux-project`)
- [ ] Fork LUX repositories; establish upstream tracking branch
- [x] Build `nlux-backend` (FastAPI + SQLite/PostgreSQL) — replaces MarkLogic (2026-04-04)
- [ ] Deploy `lux-frontend` + `nlux-backend` locally with Docker
- [ ] Ingest one Dutch institution's sample data (e.g. Teylers)
- [x] Set up NLUX documentation site (this repo)
- [ ] Define governance and contribution guidelines

### Phase 1 — Pilot (Months 4–9)
- [ ] Dutch i18n for the frontend
- [ ] Minimal branding customisation
- [ ] Data pipeline for 2–3 pilot institutions
- [ ] Staging environment (GitHub Pages frontend + hosted backend)
- [ ] Demo for pilot institutions; collect feedback
- [ ] Apply for first funding round (NWO, Creative Industries Fund NL, or EU)

### Phase 2 — Production (Months 10–18)
- [ ] Production infrastructure (SURF or Hetzner)
- [ ] Onboard pilot institutions formally (MOUs / data agreements)
- [ ] OpenSearch backend evaluation
- [ ] Public launch
- [ ] Submit to Dutch Open Science / GLAM networks

### Phase 3 — Growth (18+ Months)
- [ ] Additional institutions
- [ ] Federated search / cross-institutional entity linking
- [ ] API for third-party applications
- [ ] Community governance (steering group, working groups)

---

## 10. Risks and Mitigations

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| MarkLogic licence cost | Resolved | Replaced by `nlux-backend` (FastAPI/PostgreSQL); MarkLogic not used |
| LUX upstream divergence | Medium | Upstream tracking branch; active upstream participation |
| Institution data quality | High | Data cleaning pipeline; incremental onboarding |
| Funding gaps | Medium | Multiple funding sources; low fixed costs |
| GDPR compliance | Medium | Legal review per institution; lean on existing policies |
| Single maintainer dependency | High | Document everything; recruit volunteer contributors early |

---

## 11. Open Source & Licensing

- NLUX code: **Apache License 2.0**
- LUX upstream code: check each repo's licence (currently varies; some are Apache 2.0)
- Data contributed by institutions: institution defines licence; NLUX recommends CC0 or CC-BY
- Documentation: **CC-BY 4.0**

All forks and NLUX-specific code will be published under the `nlux-project` GitHub organisation.

---

*End of Technical Implementation Plan v0.1.0-draft*
