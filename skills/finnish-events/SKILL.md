---
name: finnish-events
description: >-
  Find events happening in Finland (Helsinki region and beyond) from the command line via
  LinkedEvents — concerts, exhibitions, children's events, sports, and more. Use whenever the
  user asks what's on, what events are happening, or for things to do in Finland.
---

# Finnish events — LinkedEvents (CLI)

Key-less. Free-text search; `include=location` expands the venue; `start=today` for upcoming.

```bash
curl -s 'https://api.hel.fi/linkedevents/v1/event/?text=jazz&page_size=5&include=location&start=today&sort=start_time' \
  | jq '.data[] | {name:(.name.fi // .name.en), start:.start_time, place:(.location.name.fi // .location.name.en)}'
```

Names, descriptions and place names are localized objects (`fi`/`en`/`sv`). Filter by date
with `start=`/`end=` (YYYY-MM-DD), or by keyword sets via `keyword=`.

**Prefer the MCP tool:** `events_search`. Data: LinkedEvents (City of Helsinki et al.).
