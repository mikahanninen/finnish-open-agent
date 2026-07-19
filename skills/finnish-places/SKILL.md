---
name: finnish-places
description: >-
  Geocode Finnish places and addresses from the command line via the National Land Survey
  (Maanmittauslaitos) — turn a place name or street address into coordinates. Use whenever the
  user needs coordinates for a Finnish location or address lookup.
---

# Finnish geocoding — National Land Survey (CLI)

Needs a free NLS API key (register at maanmittauslaitos.fi). Place/address → WGS84 coordinates:

```bash
curl -s 'https://avoin-paikkatieto.maanmittauslaitos.fi/geocoding/v2/pelias/search?text=Mannerheimintie%201&crs=EPSG:4326&api-key=YOUR_KEY' \
  | jq '.features[0] | {label:.properties.label, coords:.geometry.coordinates}'
```

Reverse geocode with `.../pelias/reverse?point.lat=60.17&point.lon=24.94&...`.

**Prefer the MCP tool:** `places_geocode`. Attribute: National Land Survey of Finland (MML).
