---
name: finnish-library
description: >-
  Find Finnish public libraries and their opening hours from the command line via the
  Kirjastot.fi API. Use whenever the user asks about a Finnish library (kirjasto), where a
  library is, or when a library is open.
---

# Finnish libraries — Kirjastot.fi (CLI)

Key-less. Search by name with `q=` (use `city.name=` to filter by municipality); add
`with=schedules` and a date range for opening hours.

```bash
D=$(date +%F)
curl -s "https://api.kirjastot.fi/v4/library?q=Oodi&lang=en&with=schedules&period.start=$D&period.end=$D" \
  | jq '.items[] | {name, city:.address.city, today:.schedules[0].times}'
```

All libraries in a city:

```bash
curl -s 'https://api.kirjastot.fi/v4/library?city.name=Tampere&lang=en&limit=20' | jq '.items[].name'
```

**Prefer the MCP tool / CLI:** `library_search` (e.g.
`finnish-open-agent call library_search query=Oodi --json`). Data: Kirjastot.fi.
