---
name: finnish-places
description: >-
  Geocode Finnish places and addresses from the command line via the National Land Survey
  (Maanmittauslaitos) — turn a place name or street address into coordinates. Use whenever the
  user needs coordinates for a Finnish location or address lookup.
---

# Finnish geocoding — National Land Survey (CLI)

Needs a free NLS API key (register at maanmittauslaitos.fi). Send it as HTTP Basic auth
(key as username, blank password) rather than the `api-key=` query-string alternative MML
also documents — query-string keys leak into proxy/access logs and browser history.
Place/address → WGS84 coordinates:

```bash
curl -s -u "$NLS_API_KEY:" 'https://avoin-paikkatieto.maanmittauslaitos.fi/geocoding/v2/pelias/search?text=Mannerheimintie%201&crs=EPSG:4326' \
  | jq '.features[0] | {label:.properties.label, coords:.geometry.coordinates}'
```

Reverse geocode with `.../pelias/reverse?point.lat=60.17&point.lon=24.94&...` (same `-u` auth).

**Prefer the MCP tool:** `places_geocode`. Attribute: National Land Survey of Finland (MML).
