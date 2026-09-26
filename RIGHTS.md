# Rights & Licensing Overview — Collection Data and Images

Assessment date: 2025 — based on rights metadata embedded in the loaded demo
records (scanned programmatically across all seven collections), the
institutions' published policies, and Dutch/EU copyright law.

**This is an engineering read of embedded metadata plus published policies,
not legal advice.** The per-record rights statements recorded in the data are
authoritative for what is *in the data*; commercial deployment decisions
(prints, merchandise, AI training, etc.) need a real legal check per
institution. Licences at institutions can change — re-verify before
production use.

## Scope

The nlux demo database currently holds **2,620 records** from seven
collections, published through the nlux API and the carousel:

| Collection | Institution | Records |
|---|---|---|
| `teylers` | Teylers Museum, Haarlem | 200 |
| `nha` | Noord-Hollands Archief, Haarlem | 408 |
| `hvh` | Huis van Hilde, Castricum | 400 |
| `fhm` | Frans Hals Museum, Haarlem | 400 |
| `wfm` | Westfries Museum, Hoorn | 400 |
| `rma` | Rijksmuseum, Amsterdam | 406 |
| `rbhc` | Rijksmuseum Boerhaave, Leiden | 406 |

## Rights overview table

| Institution | Metadata rights | Image rights | ✅ You can | ⛔ You cannot / watch out |
|---|---|---|---|---|
| **Rijksmuseum** (rma) | **CC0** — embedded in every record (`subject_to` on the data page) | Per-object at source; sampled VisualItem was marked **InC** (Copyright); some DigitalObjects flagged "niet downloadbaar" | Use, share, adapt, even commercially — all metadata; no attribution required (credit is good practice) | Assume images are free — 20th-century works are often still InC |
| **Noord-Hollands Archief** (nha) | RightsStatements per record: **349 PDM**, 31 InC, 5 CNE | Same per-record class | Use the Public-Domain-Marked records freely, incl. images; reuse all metadata under the Woo (government body) with source mention | Use the 31 InC images without permission; assume the 5 CNE (not evaluated) are safe |
| **Huis van Hilde** (hvh) | **CC BY-NC-ND 3.0 NL** (`dc_rights` in records: "Naamsvermelding-NietCommercieel-GeenAfgeleideWerken 3.0 Nederland") | Same licence | Share for **non-commercial** purposes **with attribution** (carousel already credits "Huis van Hilde, Castricum") | Use commercially; make derivatives (recolor, collage, crop into new works); drop the credit |
| **Teylers Museum** (teylers) | None recorded — all rights reserved default | None recorded; Adlib-served (teylers.adlibhosting.com); records carry provenance credit lines, not copyright statements | Display in demo/research with credit; underlying works (Michelangelo, Rembrandt drawings, fossils) are public domain | Assume open reuse — private foundation, API terms reserve rights; some photos may be © photographer |
| **Frans Hals Museum** (fhm) | None recorded; municipal museum → Woo applies | Occasional "Frans Hals Museum, Haarlem" credit in records; museum photography can carry own rights | Reuse metadata with source mention (Woo); faithful reproductions of the PD paintings are free (HR 2019, below) | Blanket-reuse their photos; the **modern photography collection** can be 70-yrs-pma InC |
| **Rijksmuseum Boerhaave** (rbhc) | None recorded — all rights reserved default | None recorded; Adlib-served (mmb-web.adlibhosting.com) | Display in demo with credit; old scientific instruments are PD works | Assume open reuse — photos of 3D objects are themselves creative works of the photographer |
| **Westfries Museum** (wfm) | None recorded — all rights reserved default | Memorix-served (images.memorix.nl), no rights fields | Display in demo with credit; Golden Age objects are PD works | Assume open reuse — private foundation, no statutory open-data regime |

Key takeaway: **"available online via API" does not mean "under a licence."**
Only two of the seven collections embed one (Rijksmuseum: CC0; Huis van Hilde:
CC BY-NC-ND 3.0 NL). Where nothing is stated, copyright law defaults to *all
rights reserved*, with the underlying public-domain works themselves still free.

## How this was determined

Rights metadata was scanned in the loaded records
(`backend/sample_data/*_mapped/`) and the raw harvest input
(`$LUX_BASEPATH/data/input/<source>/`):

- **rma**: `subject_of[.].subject_to` → `Right` classified as
  `https://creativecommons.org/publicdomain/zero/1.0/` in 406/406 records;
  per-image rights live on separate VisualItem/DigitalObject resources at
  `id.rijksmuseum.nl` (sample: `rightsstatements.org/vocab/InC/1.0/`).
- **nha**: `referred_to_by` notes carrying RightsStatements.org classes —
  "PDM 1.0 Geen auteursrecht" (349), "InC 1.0 Auteursrechtelijk beschermd"
  (31), "CNE 1.0 Auteursrechtelijke status niet geëvalueerd" (5); the
  remaining loaded records carry no rights note.
- **hvh**: `dc_rights` field with "Naamsvermelding-NietCommercieel-
  GeenAfgeleideWerken 3.0 Nederland" (CC BY-NC-ND 3.0 NL).
- **teylers / fhm / wfm / rbhc**: no rights/licence URIs or rights statements
  found in the records; only provenance credit lines (teylers `credit_line`,
  fhm `copyright` credit "Frans Hals Museum, Haarlem").

## Legal framework (NL/EU — there is no US "fair use")

- **Copyright defaults to all rights reserved.** Absence of a licence means
  nothing is permitted beyond statutory exceptions.
- **Hoge Raad, 22 November 2019** (ECLI:NL:HR:2019:1795): a faithful
  photographic reproduction of a **2D public-domain work** (paintings,
  drawings, prints — Hals, Rembrandt) carries **no new copyright**. Those
  images are free even if the museum claims otherwise. This does **not**
  extend to photos of **3D objects** (instruments, artefacts) — those are
  creative works of the photographer (70 yrs post mortem auctoris).
- **Statutory exceptions**: *citaatrecht* (quotation right, art. 15
  Auteurswet) allows quoting in context; *portretrecht* (art. 21 Auteurswet)
  protects depicted persons — relevant for the photo collections (NHA, FHM).
- **Wet open overheid (Woo)**: government bodies (Noord-Hollands Archief,
  Frans Hals Museum, Huis van Hilde, arguably Rijksmuseum Boerhaave) make
  their data reusable with source attribution, unless excepted. Private
  foundations (Teylers, Westfries, Rijksmuseum) have no statutory open-data
  regime.
- **Database right** (Databankenbesluit): bulk systematic extraction of an
  entire catalogue could engage the *sui generis* databankrecht; per-record
  API use does not.

## Practice notes for the nlux platform

- The demo's position is reasonable: every collection is credited (carousel
  credit lines), images are proxied server-side rather than hotlinked, and
  the showcase is non-commercial — but it is still *making available online*,
  so:
  - the InC/CNE records (Noord-Hollands Archief) and unmarked photo rights
    deserve a **takedown contact** (e.g. in the footer, using the existing
    institution list);
  - keep Huis van Hilde usage non-commercial, attributed, and non-derivative
    (plain display at reduced size is a faithful reproduction, not a
    derivative).
- Future iteration: **surface the per-record rights class in the API and
  detail pages**. The data is already there for rma/nha/hvh — the backend
  currently does not expose it as a field.