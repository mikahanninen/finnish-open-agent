---
name: finnish-culture
description: >-
  Finnish cultural heritage from the command line via Finna — search books, images,
  recordings, objects, and archival material across Finnish libraries, museums, and archives.
  Use whenever the user asks to find Finnish cultural, museum, library, or archive materials.
---

# Finnish cultural heritage — Finna (CLI)

Finna (National Library of Finland) aggregates records from hundreds of institutions. No key.
Each record page is `https://www.finna.fi/Record/<id>`.

```bash
curl -s 'https://api.finna.fi/v1/search?lookfor=Tove%20Jansson&limit=5&field%5B%5D=title&field%5B%5D=id&field%5B%5D=year&field%5B%5D=formats&field%5B%5D=buildings' \
  | jq '.records[] | {title, year, id}'
```

Filter with facets, e.g. only images: add `&filter[]=format:0/Image/`. Restrict to one
organisation: `&filter[]=building:0/Museovirasto/`.

**Prefer the MCP tool:** `culture_search`. Attribute each holding organisation as shown in the
record's `buildings`/`institutions`.
