# Branding Configuratie

NLUX ondersteunt een kleine set branding-opties zonder structurele wijzigingen in de upstream `lux-frontend` codebase. De bedoeling is een rustige, minimale look te krijgen door alleen configuratie aan te passen.

## Beschikbare opties

De frontend leest onderstaande waarden uit `config.json` in Docker, of uit environment variables wanneer je de frontend los draait.

| Optie | Voorbeeld | Effect |
|------|------|------|
| `NLUX_LOGO` | `/nlux-logo.png` | Vervangt de teksttitel in de header door een logo-afbeelding |
| `NLUX_PRIMARY_COLOR` | `#1F2937` | Achtergrondkleur van de hoofdheader |
| `NLUX_SECONDARY_COLOR` | `#D1D5DB` | Gereserveerd voor secundaire accenten |
| `NLUX_FONT_COLOR` | `#F9FAFB` | Tekstkleur van navigatie-items in de header |

## Docker-configuratie

De standaard lokale configuratie staat in `docker/frontend-config.json`. Bij `docker compose up` wordt die in de frontend-container gemount als runtime-configuratie.

Daarnaast mount NLUX het standaardlogo vanuit de repo naar `/nlux-logo.png`, zodat de configuratie direct werkt zonder extra handmatige stappen.

## Losse frontend

Wanneer je `lux-frontend` buiten Docker draait, kun je dezelfde waarden zetten via environment variables:

```bash
NLUX_LOGO=/nlux-logo.png
NLUX_PRIMARY_COLOR=#1F2937
NLUX_SECONDARY_COLOR=#D1D5DB
NLUX_FONT_COLOR=#F9FAFB
```

Voor Vite/local client overrides zijn ook `REACT_APP_NLUX_LOGO`, `REACT_APP_NLUX_PRIMARY_COLOR`, `REACT_APP_NLUX_SECONDARY_COLOR` en `REACT_APP_NLUX_FONT_COLOR` beschikbaar.

## Huidige standaard

De meegeleverde standaard gebruikt een neutraal donkergrijs headervlak met lichte typografie. Dat sluit aan op de gewenste minimalistische NLUX-richting, terwijl de bestaande frontend-layout intact blijft.
