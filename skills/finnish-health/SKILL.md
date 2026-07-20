---
name: finnish-health
description: >-
  Finnish health & welfare statistics from the command line via THL Sotkanet — thousands of
  indicators (obesity, unemployment, alcohol use, care coverage…) by region and year. Use when
  the user asks about Finnish health, welfare, wellbeing, or social statistics.
---

# Finnish health & welfare — THL Sotkanet (CLI)

Key-less. Find an indicator id, then fetch its value (whole country = region id 658).

```bash
# search indicators (English or Finnish titles)
curl -s 'https://sotkanet.fi/rest/1.1/indicators' \
  | jq '[.[] | select(.title.en|test("obesity";"i")) | {id, title:.title.en}][:5]'

# value for an indicator/year (filter region 658 = whole country client-side)
curl -s 'https://sotkanet.fi/rest/1.1/json?indicator=127&years=2022&genders=total' \
  | jq '.[] | select(.region==658)'
```

Region ids come from `https://sotkanet.fi/rest/1.1/regions` (658 = Whole country). Not every
indicator has every year/region.

**Prefer the MCP tools:** `health_search_indicators`, `health_get_indicator`. Data: THL Sotkanet.
