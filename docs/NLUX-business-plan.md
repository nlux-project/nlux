# NLUX Business Plan

**Version:** 0.1.0-draft  
**Date:** 2026-04-03  
**Status:** Draft — Initial outline for funding applications and organisational participation

---

## Executive Summary

NLUX is an open-source collections discovery platform for Dutch Cultural Heritage institutions. It provides a modern, standards-based (Linked.art / CIDOC-CRM) way to explore and interconnect museum and heritage collections online. Built on Yale University's proven LUX platform, NLUX reduces the cost and technical complexity for Dutch institutions to offer world-class digital discovery to their audiences.

NLUX is organised as a not-for-profit, open-source project. Revenue is generated through implementation services, consulting, training, and grant funding — not through licensing or data lock-in. All software and data standards remain open.

---

## 1. Problem Statement

Dutch cultural heritage institutions — museums, archives, libraries — hold world-class collections. Their digital discovery infrastructure is fragmented:

- Each institution runs a separate, siloed online collection system.
- Cross-institutional search is either absent or limited to aggregators (Europeana, Erfgoed Leiden) that normalise data to a low common denominator.
- Integration with global linked data ecosystems (Wikidata, Getty, VIAF) is inconsistent.
- Small and medium institutions lack the IT capacity and budget to build modern discovery platforms.

LUX, developed by Yale University, solves exactly this problem for Yale's libraries and museums. NLUX brings this solution to the Netherlands.

---

## 2. Solution

NLUX provides:

1. **A shared platform**: one installation serves multiple institutions, reducing per-institution cost.
2. **Linked data at the core**: collections are described in Linked.art (CIDOC-CRM), enabling cross-institutional entity linking and integration with internationally shared authority files (AAT, Wikidata, RKD, NTA).
3. **Open source**: institutions are never locked into a vendor; the code is publicly auditable and improvable.
4. **LUX compatibility**: NLUX stays 100% compatible with Yale LUX, giving Dutch institutions access to a large, sustained upstream project.
5. **Dutch localisation**: Dutch-language interface, Dutch authority files, and alignment with Dutch standards (NDE, DERA).

---

## 3. Target Market

### Primary: Dutch Cultural Heritage Institutions

Small to medium institutions with collections online but limited digital capacity:

| Institution | Location | Collection Focus |
|-------------|----------|-----------------|
| Teylers Museum | Haarlem | Natural history, art, scientific instruments |
| Museum Boerhaave | Leiden | History of science and medicine |
| Huis van Hilde | Castricum | Archaeological finds, North Holland |
| RMO (Rijksmuseum van Oudheden) | Leiden | Archaeology, ancient civilisations |

Additional prospects: regional archeological services (ADC, BAAC), provincial museums, art museums outside the Randstad.

### Secondary: Aggregators and Infrastructure Providers

- **NDE (Netwerk Digitaal Erfgoed)**: national digital heritage network; NLUX contributes to their linked data ambitions.
- **KBNL (Koninklijke Bibliotheek)**: national library; potential data contributor and partner.
- **Europeana**: NLUX can feed standardised Linked.art data into Europeana.

---

## 4. Revenue Model

NLUX operates as a not-for-profit project. Revenue streams:

### 4.1 Implementation Services (Primary)
Institutions pay for:
- Data mapping and migration from Adlib / Axiell EMu / TMS to Linked.art
- Custom connectors for their collection management systems
- Deployment and integration with existing IT infrastructure
- Staff training

**Estimated rate:** €900–1,500/day consulting; €15,000–60,000 per institution onboarding project.

### 4.2 Hosting / Managed Service
Optionally, NLUX can offer a managed hosting service:
- Monthly fee per institution: €300–800/month (small–medium).
- Covers infrastructure, monitoring, updates, and support.

### 4.3 Grants and Public Funding
Dutch and European funding programmes aligned with NLUX's mission:

| Funder | Programme | Notes |
|--------|-----------|-------|
| NWO | SSH Open Science | Research data / open infrastructure |
| Creative Industries Fund NL | Digital culture | UX & design aspects |
| RCE / OCW | Erfgoedprogramma's | Cultural heritage digitisation |
| EU Horizon Europe | Research Infrastructures | Cross-border linked data |
| EU Digital Europe | Cultural heritage | Digital transformation |
| SURF | SURF Open Innovation Lab | Dutch research infrastructure |
| Dutch Postcode Lottery | Cultural heritage | Social impact focus |
| Private foundations | Van den Broek, Prins Bernhard Cultuurfonds | Heritage-specific |

**Target per grant cycle:** €50,000–250,000.

### 4.4 Sponsorship
Corporate sponsors (e.g. technology companies with a heritage / open source interest) can sponsor development of specific features or infrastructure.

### 4.5 Talks, Training, and Publications
Conference talks (DH, Museums & Web, Linked Data events), workshops, and published guides generate income and visibility.

---

## 5. Cost Structure

### One-Time / Setup Costs (Year 1)

| Item | Estimated Cost |
|------|---------------|
| Legal setup (foundation / stichting) | €500–1,500 |
| Accountant / notary | €1,000–2,000 |
| Domain, branding, design | €2,000–5,000 |
| Initial infrastructure setup | €2,000–5,000 |
| Travel (stakeholder meetings) | €2,000–4,000 |
| **Total setup** | **€7,500–17,500** |

### Recurring Costs (Annual)

| Item | Estimated Cost/Year |
|------|-------------------|
| Infrastructure (hosting, CI/CD) | €3,000–8,000 |
| MarkLogic licence (if used) | €0 (Developer) – €10,000+ (negotiated) |
| Accountant / legal | €2,000–4,000 |
| Insurance | €500–1,000 |
| Travel / events | €3,000–6,000 |
| **Total recurring** | **€8,500–29,000** |

### Personnel

Initially the project is maintained by a single person (founder / lead). Target state within 2 years:
- 1 FTE lead developer / project manager (founder)
- 0.5 FTE data engineer (grant-funded or institutional secondment)
- Community contributors (volunteer)

**Break-even consulting revenue needed (Year 1):** approximately €40,000–60,000 gross, assuming low overhead and partial grant funding.

---

## 6. Legal Structure

### Recommended Form: Stichting (Foundation)

A Dutch *Stichting* (foundation) is the standard legal form for non-profit open source and cultural projects in the Netherlands:

- No shareholders; profits are reinvested in the mission.
- Can receive grants and donations.
- Can employ staff and enter into contracts.
- Board (bestuur) of minimum 1 person; recommended 3–5 for governance and credibility.
- Low setup cost (~€500–1,000 notary fee).

### Governance

- **Board**: founder + 2–4 external members (heritage sector, technology, legal/finance).
- **Advisory board / user group**: representatives from pilot institutions.
- **Open source project governance**: contribution guidelines, code of conduct, RFC process for major changes.

### Intellectual Property

- All NLUX-produced source code: Apache License 2.0.
- Trademarks (name, logo): held by the Stichting.
- Data contributed by institutions: remains the property of the institution; licenced to NLUX for aggregation and display.

### Contracts with Institutions

- Memoranda of Understanding (MOUs) for pilot phase (no payment required).
- Service agreements for production onboarding and hosting.
- Data sharing agreements specifying licence, attribution, and withdrawal rights.

---

## 7. Partnerships

| Partner | Role |
|---------|------|
| Yale / Project LUX | Upstream codebase; reference implementation |
| NDE (Netwerk Digitaal Erfgoed) | Alignment with Dutch digital heritage strategy |
| DANS / SURF | Hosting and research infrastructure |
| RKD (Netherlands Institute for Art History) | Authority file integration (RKDartists) |
| KB Nationale Bibliotheek | NTA authority file; potential pilot partner |
| Linked.art community | Data model governance |
| Europeana | Data aggregation and visibility |

---

## 8. Competitive Landscape

| Platform | Organisation | Notes |
|----------|-------------|-------|
| LUX | Yale University | Upstream; NLUX is built on this |
| CollectiveAccess | Open source community | Collection management, not discovery |
| Omeka | Roy Rosenzweig Center | Publishing, not full CMS |
| Ibexa / Civica | Commercial | Vendor lock-in, expensive |
| Europeana | EU | Aggregator, low metadata granularity |
| IIIF viewers | Various | Viewer layer only, not search/discovery |

NLUX occupies a unique position: open source, LUX-compatible, Dutch-localised, and offering a full discovery experience (not just a viewer or aggregator).

---

## 9. Key Milestones (Business)

| Milestone | Target Date | Notes |
|-----------|------------|-------|
| Stichting incorporated | Month 3 | Required for grant applications |
| First MOU signed | Month 6 | Teylers or Boerhaave as pilot |
| First grant application submitted | Month 4 | NDE or Creative Industries Fund |
| First grant awarded | Month 9–12 | Dependent on funder cycle |
| First paying client | Month 9–12 | Implementation services |
| Break-even | Month 18–24 | Mix of services + grants |

---

## 10. Risks

| Risk | Mitigation |
|------|-----------|
| Too dependent on single founder | Recruit board members and community early |
| Grant application rejected | Multiple parallel applications; low fixed costs |
| MarkLogic licensing cost | Open stack alternative in parallel roadmap |
| Institutions slow to commit | Start with MOUs; reduce barrier to entry |
| LUX upstream goes closed | Apache licence protects existing forks; open stack fallback |
| GDPR / legal complexity | Legal advisory board member; per-institution review |

---

## 11. Three-Year Financial Projection (Rough)

|  | Year 1 | Year 2 | Year 3 |
|--|--------|--------|--------|
| Implementation revenue | €20,000 | €60,000 | €120,000 |
| Hosting / managed service | €0 | €10,000 | €25,000 |
| Grants | €30,000 | €80,000 | €100,000 |
| Sponsorship | €5,000 | €10,000 | €20,000 |
| Talks / training | €5,000 | €10,000 | €15,000 |
| **Total revenue** | **€60,000** | **€170,000** | **€280,000** |
| Operating costs | €25,000 | €50,000 | €80,000 |
| Personnel | €40,000 | €90,000 | €140,000 |
| **Net** | **-€5,000** | **€30,000** | **€60,000** |

*Note: Year 1 assumes founder draws partial salary; grant funding bridges shortfall.*

---

*End of Business Plan v0.1.0-draft*
