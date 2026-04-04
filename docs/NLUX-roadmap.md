# NLUX Unified Roadmap

**Version:** 0.2.0-draft  
**Date:** 2026-04-04  
**Status:** Draft

This document combines milestones from the Technical Implementation Plan, Business Plan, and Marketing Plan into a single timeline. Each milestone is tagged with its domain:

- `[TECH]` — Technical Implementation Plan
- `[BIZ]` — Business Plan
- `[MKT]` — Marketing Plan
- `[LEGAL]` — Legal / Governance

---

## Phase 0 — Foundation (Months 1–3, target: Q2 2026)

Goal: establish the project's legal, organisational, and technical foundation.

| # | Milestone | Domain | Notes |
|---|-----------|--------|-------|
| 0.1 | Register GitHub organisation (`nlux-project`) | `[TECH]` | Fork LUX repos; set up upstream tracking branches |
| 0.2 | Build `nlux-backend` (FastAPI/SQLite/PostgreSQL) | `[TECH]` | Replaces MarkLogic; compatible with lux-frontend API — **done 2026-04-04** |
| 0.3 | Deploy `lux-frontend` + `nlux-backend` locally (Docker) | `[TECH]` | Validate full stack runs end-to-end |
| 0.4b | Ingest Teylers Museum sample data into `nlux-backend` | `[TECH]` | First real Dutch dataset via `load_data.py` |
| 0.4 | Set up NLUX documentation site (this MkDocs repo) | `[TECH]` | Published to GitHub Pages |
| 0.5 | Define contribution guidelines and code of conduct | `[TECH]` `[LEGAL]` | Contributor Covenant; CONTRIBUTING.md |
| 0.6 | Incorporate Stichting NLUX with notary | `[LEGAL]` `[BIZ]` | Required before grant applications |
| 0.7 | Appoint initial board (3 members minimum) | `[LEGAL]` `[BIZ]` | Recruit 2 external board members |
| 0.8 | Open private conversations with Teylers and Boerhaave | `[BIZ]` `[MKT]` | No commitment required; gauge interest |
| 0.9 | Register domain (`nlux.nl` or `nlux-project.org`) | `[MKT]` | DNS, basic landing page |
| 0.10 | ~~Agree on MarkLogic strategy~~ → decided: `nlux-backend` | `[TECH]` `[BIZ]` | MarkLogic ruled out; FastAPI/PostgreSQL backend built — **done 2026-04-04** |

**Phase 0 exit criteria:** Stichting incorporated; LUX running locally with Dutch sample data; at least 2 institutions in conversation.

---

## Phase 1 — Pilot (Months 4–9, target: Q3–Q4 2026)

Goal: visible proof-of-concept, first formal partners, first grant application.

| # | Milestone | Domain | Notes |
|---|-----------|--------|-------|
| 1.1 | Dutch (nl) i18n for LUX frontend | `[TECH]` | Adds Dutch locale; no structural changes |
| 1.2 | Minimal NLUX branding (logo, colours) via config | `[TECH]` | Environment variables / theme config only |
| 1.3 | Data pipeline for Teylers Museum (Adlib/Axiell → Linked.art) | `[TECH]` | Custom connector; published as open source |
| 1.4 | Staging environment (GitHub Pages + hosted backend) | `[TECH]` | Publicly accessible demo URL |
| 1.5 | Security and GDPR review of staging environment | `[TECH]` `[LEGAL]` | Before sharing with institutions |
| 1.6 | Sign first MOU (Teylers or Boerhaave) | `[BIZ]` `[LEGAL]` | Template MOU; no payment required at pilot stage |
| 1.7 | Submit first grant application (NDE or Creative Industries Fund NL) | `[BIZ]` | Stichting required; aim for ≥€30,000 |
| 1.8 | Soft launch: announce at NDE event or working group | `[MKT]` | Present demo; publish GitHub org and docs site |
| 1.9 | Collect feedback from pilot institutions | `[TECH]` `[BIZ]` | Structured interviews; feed into Phase 2 backlog |
| 1.10 | Publish first case study (Teylers pilot) | `[MKT]` | Blog post + documentation page |
| 1.11 | Open source release: tag `v0.1.0` on all NLUX repos | `[TECH]` | Semantic versioning begins |

**Phase 1 exit criteria:** Live demo with real institutional data; at least 1 MOU signed; 1 grant application submitted; public GitHub organisation visible.

---

## Phase 2 — Production (Months 10–18, target: Q1–Q3 2027)

Goal: first production deployment, paying clients, first grant award.

| # | Milestone | Domain | Notes |
|---|-----------|--------|-------|
| 2.1 | Production infrastructure (SURF or Hetzner) | `[TECH]` | Replaces staging; SLA-backed |
| 2.2 | Formal onboarding of pilot institutions (service agreements) | `[BIZ]` `[LEGAL]` | First recurring revenue |
| 2.3 | Data pipelines for 2–3 institutions | `[TECH]` | Reuse and extend Teylers connector |
| 2.4 | OpenSearch backend evaluation | `[TECH]` | Parallel to MarkLogic; compare search quality |
| 2.5 | Public launch | `[MKT]` | Press release; institution pages live |
| 2.6 | First grant awarded | `[BIZ]` | Fund data engineer (0.5 FTE) |
| 2.7 | Submit talk proposals (Museums & Web, DH Benelux) | `[MKT]` | Abstract submission deadlines vary |
| 2.8 | Launch newsletter | `[MKT]` | Target 200 subscribers by end of phase |
| 2.9 | Recruit first community contributor | `[TECH]` | Open issues labelled `good first issue` |
| 2.10 | Tag `v1.0.0` — first production release | `[TECH]` | Changelog; migration guide from v0.x |
| 2.11 | User group / steering group first meeting | `[LEGAL]` `[BIZ]` | Formalise institutional participation |

**Phase 2 exit criteria:** Production deployment live; ≥2 paying institutions; first grant funding received; `v1.0.0` tagged.

---

## Phase 3 — Growth (Months 19–36, target: Q4 2027–Q2 2028)

Goal: sustainable operation, community growth, cross-institutional entity linking.

| # | Milestone | Domain | Notes |
|---|-----------|--------|-------|
| 3.1 | Onboard 3–5 additional institutions | `[BIZ]` `[TECH]` | Standardised onboarding playbook |
| 3.2 | Cross-institutional entity linking (persons, objects, places) | `[TECH]` | Wikidata / RKD reconciliation pipeline |
| 3.3 | Public SPARQL endpoint | `[TECH]` | For researchers and third-party apps |
| 3.4 | OpenSearch backend production migration (if validated) | `[TECH]` | Removes MarkLogic dependency |
| 3.5 | Second major grant application (EU Horizon / Digital Europe) | `[BIZ]` | Requires track record and partners |
| 3.6 | Bilateral partnership with Flemish / Belgian institution | `[BIZ]` `[MKT]` | FARO or a Flemish museum |
| 3.7 | Annual NLUX community event | `[MKT]` | Workshop day; hybrid format |
| 3.8 | Financial sustainability review | `[BIZ]` | Board reviews 3-year projection; adjust strategy |
| 3.9 | Contribution back to Yale LUX upstream | `[TECH]` | PRs, bug reports, or feature proposals |

**Phase 3 exit criteria:** Organisation financially self-sustaining (no dependency on single grant); ≥5 active institutions; active community of contributors.

---

## Dependencies and Critical Path

```
0.6 Stichting incorporated
  └── 1.6 First MOU
  └── 1.7 First grant application
        └── 2.6 First grant awarded
              └── 3.5 EU grant application

0.2 LUX running locally
  └── 0.3 Teylers sample data
        └── 1.3 Teylers pipeline
              └── 1.4 Staging environment
                    └── 2.1 Production infrastructure

0.2 nlux-backend built (FastAPI/SQLite/PostgreSQL)
  └── 0.3 Deploy lux-frontend + nlux-backend locally
        └── 0.4b Ingest Teylers sample data
              └── 1.4 Staging environment
                    └── 2.4 OpenSearch evaluation (optional)
                          └── 3.4 OpenSearch migration (optional)
```

---

## Key Risks by Phase

| Phase | Top Risk | Mitigation |
|-------|----------|-----------|
| 0 | Stichting setup delayed (notary availability) | Start process immediately; use template statuten |
| 1 | Institutions not ready to sign an MOU | Lower barrier: informal letter of intent first |
| 2 | Grant application rejected | Multiple parallel applications; NDE + Creative Industries |
| 2 | nlux-backend search quality at scale | Evaluate OpenSearch as Phase 2 backend if PostgreSQL FTS insufficient |
| 3 | Single founder burnout | Recruit board and contributors before Phase 3 begins |

---

## Document Cross-References

| Topic | Detail in |
|-------|----------|
| Architecture & tech stack | [NLUX-technical-implementation-plan.md](NLUX-technical-implementation-plan.md) |
| Revenue, costs, projections | [NLUX-business-plan.md](NLUX-business-plan.md) |
| Channels, messaging, launch | [NLUX-marketing-plan.md](NLUX-marketing-plan.md) |
| Mission, values, governance | [NLUX-mission-values.md](NLUX-mission-values.md) |

---

*End of Unified Roadmap v0.1.0-draft*
