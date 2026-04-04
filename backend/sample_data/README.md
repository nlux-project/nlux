# Sample data

This directory contains example Linked Art JSON-LD records for each entity type
supported by nlux-backend. Use these as templates when preparing institution data.

## Loading data

```bash
python scripts/load_data.py sample_data/
```

## Required fields

Every record must have:

| Field | Description | Example |
|-------|-------------|---------|
| `id` | Unique URI for this record | `https://teylers.nl/data/set/teylers-tekeningen` |
| `type` | Linked Art entity type (see below) | `Set` |
| `_label` | Human-readable display label | `Teylers Museum – Tekeningen` |

## Entity types and search scopes

| Linked Art type(s) | lux-frontend scope | Tab |
|--------------------|--------------------|-----|
| `HumanMadeObject`, `DigitalObject` | `item` | Objects |
| `LinguisticObject`, `VisualItem` | `work` | Works |
| `Set` | `set` | Collections |
| `Person`, `Group`, `Actor` | `agent` | People & Groups |
| `Place` | `place` | Places |
| `Type`, `Material`, `Language`, `MeasurementUnit`, `Currency` | `concept` | Concepts |
| `Activity`, `Period`, `Event` | `event` | Events |

## Set (Collection)

A `Set` groups related objects into a named collection. Required to populate
the "Collections" tab in lux-frontend.

See [`set_example.json`](set_example.json) for a full example.

**Minimum viable Set record:**

```json
{
  "@context": "https://linked.art/ns/v1/linked-art.json",
  "id": "https://your-institution.nl/data/set/your-collection-id",
  "type": "Set",
  "_label": "Your Collection Name",
  "identified_by": [
    {
      "type": "Name",
      "content": "Your Collection Name",
      "classified_as": [
        {
          "id": "http://vocab.getty.edu/aat/300404670",
          "type": "Type",
          "_label": "preferred name"
        }
      ]
    }
  ]
}
```

## HumanMadeObject

Physical museum objects. These are the most common records and are already
present in the Teylers test dataset
(`github.com/jsoeterbroek/teylers_collection_research/lux_metadata`).

Key fields:
- `produced_by` — production event with `carried_out_by` (actor) and `timespan`
- `made_of` — materials array
- `identified_by` — names and accession numbers
- `referred_to_by` — descriptions, inscriptions, acquisition notes

## Notes on URIs

- URIs must be globally unique and stable
- Use `https://your-institution.nl/data/{type}/{id}` as the pattern
- The `id` field is the primary key in nlux-backend's database
- lux-frontend constructs record detail URLs from the `id` field
